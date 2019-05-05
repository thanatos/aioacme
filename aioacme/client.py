import json
from typing import Any, List, Optional

import aiohttp
import josepy.jws
from yarl import URL

from . import account
from . import authorization
from . import order as _order
from . import problem as _problem


class AcmeClient:
    def __init__(
            self,
            directory_url: str,
            directory,
            full_user_agent: str,
            aiohttp_client,
            aiohttp_client_is_owned: bool,
    ) -> None:
        self.directory_url = directory_url
        self.directory = directory
        self.aiohttp_client = aiohttp_client
        self.aiohttp_client_is_owned = aiohttp_client_is_owned
        self.user_agent = full_user_agent
        self.next_nonce = None

    async def close(self):
        if self.aiohttp_client_is_owned:
            self.aiohttp_client.close()

    async def refresh_nonce(self) -> None:
        headers = [('User-Agent', self.user_agent)]
        async with self.aiohttp_client.head(
                self.directory.new_nonce_url,
                headers=headers,
        ) as response:
            response.raise_for_status()
            self.next_nonce = response.headers['Replay-Nonce']

    async def consume_nonce(self) -> str:
        if self.next_nonce is None:
            await self.refresh_nonce()
        nonce = self.next_nonce
        self.next_nonce = None
        return nonce

    async def _get(self, url: str):
        headers = [('User-Agent', self.user_agent)]
        async with self.aiohttp_client.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def _post(self, url: str, data: bytes, headers):
        async with self.aiohttp_client.post(url, data=data, headers=headers) \
                as response:
            if 400 <= response.status:
                body = await response.read()
                if response.headers['Content-Type'] == 'application/problem+json':
                    json_ = json.loads(body)
                    problem = _problem.from_json(json_)
                    if problem is not None:
                        raise problem
                raise ErrorResponse(response.status, response.headers, body)

            self.next_nonce = response.headers['Replay-Nonce']

            if response.headers['Content-Type'] == 'application/json' \
                    or response_headers['Content-Type'].endswith('+json'):
                json_ = await response.json()
                return response.status, response.headers, json_
            else:
                raise ProtocolError(
                    'Response body was not JSON.',
                    response.status,
                    response.headers,
                    await response.read(),
                )

    async def _post_with_key_id(
            self,
            url: str,
            data: bytes,
            private_key,
            account_href: str,
    ):
        headers = [
            ('Content-Type', 'application/jose+json'),
            ('User-Agent', self.user_agent),
        ]
        nonce = await self.consume_nonce()
        jws_data = AcmeJws.sign(
            data,
            key=private_key,
            alg=josepy.jwa.RS256,
            protect=frozenset(('alg', 'url', 'kid', 'nonce')),
            include_jwk=False,
            url=url,
            kid=account_href,
            nonce=nonce,
        ).json_dumps().encode('utf-8')
        return await self._post(url, jws_data, headers)

    async def _post_json_with_key_id(
            self,
            url: str,
            json_data,
            private_key,
            account_href: str,
    ):
        return await self._post_with_key_id(
            url,
            json.dumps(json_data).encode('utf-8'),
            private_key,
            account_href,
        )

    async def new_account(
            self,
            key,
            contacts: Optional[List[URL]] = None,
            terms_of_service_agreed: Optional[bool] = None,
            external_account_binding: Optional[Any] = None,
    ):
        headers = [
            ('Content-Type', 'application/jose+json'),
            self._user_agent_header(),
        ]

        json_data = {}
        if contacts is not None:
            json_data['contacts'] = [str(contact) for contact in contacts]
        if terms_of_service_agreed is not None:
            json_data['termsOfServiceAgreed'] = terms_of_service_agreed
        if external_account_binding is not None:
            json_data['externalAccountBinding'] = external_account_binding

        nonce = await self.consume_nonce()
        jws_data = AcmeJws.sign(
            json.dumps(json_data).encode('utf-8'),
            key=key,
            alg=josepy.jwa.RS256,
            protect=frozenset(('alg', 'url', 'jwk', 'nonce')),
            url=self.directory.new_account_url,
            nonce=nonce,
        ).json_dumps().encode('utf-8')

        async with self.aiohttp_client.post(
                self.directory.new_account_url,
                data=jws_data,
                headers=headers,
        ) as response:
            response.raise_for_status()
            self.next_nonce = response.headers['Replay-Nonce']
            account_href = response.headers['Location']
            return account.Account(self, key, account_href)

    async def existing_account_from_key(self, key):
        headers = [
            ('Content-Type', 'application/jose+json'),
            ('User-Agent', self.user_agent),
        ]
        json_data = b'{"onlyReturnExisting": true}'
        nonce = await self.consume_nonce()
        jws_data = AcmeJws.sign(
            json_data,
            key=key,
            alg=josepy.jwa.RS256,
            protect=frozenset(('alg', 'url', 'jwk', 'nonce')),
            url=self.directory.new_account_url,
            nonce=nonce,
        ).json_dumps().encode('utf-8')

        async with self.aiohttp_client.post(
                self.directory.new_account_url,
                data=jws_data,
                headers=headers,
        ) as response:
            response.raise_for_status()
            self.next_nonce = response.headers['Replay-Nonce']
            account_href = response.headers['Location']
            return account.Account(self, key, account_href)

    async def get(self, url):
        headers = [self._user_agent_header()]
        async with self.aiohttp_client.get(
                str(url), headers=headers,
        ) as response:
            response.raise_for_status()
            return await response.read()

    async def fetch_order(self, order_url):
        headers = [self._user_agent_header()]
        async with self.aiohttp_client.get(
                str(order_url), headers=headers,
        ) as response:
            response.raise_for_status()
            json_data = await response.json()
            return _order.Order.from_json(json_data)

    async def fetch_authorization(self, authorization_url):
        headers = [
            self._user_agent_header(),
        ]
        async with self.aiohttp_client.get(
                str(authorization_url),
                headers=headers,
        ) as response:
            response.raise_for_status()
            json_data = await response.json()
            return authorization.authorization_from_json(json_data)

    def _user_agent_header(self):
        return ('User-Agent', self.user_agent)


async def new_client(url, user_agent, aiohttp_client=None):
    if aiohttp_client is None:
        aiohttp_client = aiohttp.ClientSession()
        aiohttp_client_is_owned = True
    else:
        aiohttp_client_is_owned = False

    try:
        full_user_agent = user_agent + ' aioacme/0.0.1.dev0'
        headers = [('User-Agent', full_user_agent)]
        async with aiohttp_client.get(url, headers=headers) as response:
            response.raise_for_status()
            directory_data = await response.json()
            directory = Directory.from_json(directory_data)
            return AcmeClient(
                url,
                directory,
                full_user_agent,
                aiohttp_client,
                aiohttp_client_is_owned,
            )
    except:  # noqa: We're cleaning up resources here.
        if aiohttp_client_is_owned:
            await aiohttp_client.close()
        raise


class Directory:
    def __init__(
            self,
            *,
            key_change_url: str,
            new_account_url: str,
            new_nonce_url: str,
            new_order_url: str,
            revoke_certificate_url: str,
    ) -> None:
        self.key_change_url = key_change_url
        self.new_account_url = new_account_url
        self.new_nonce_url = new_nonce_url
        self.new_order_url = new_order_url
        self.revoke_certificate_url = revoke_certificate_url

    @staticmethod
    def from_json(data):
        key_change_url = data['keyChange']
        new_account_url = data['newAccount']
        new_nonce_url = data['newNonce']
        new_order_url = data['newOrder']
        revoke_certificate_url = data['revokeCert']

        return Directory(
            key_change_url=key_change_url,
            new_account_url=new_account_url,
            new_nonce_url=new_nonce_url,
            new_order_url=new_order_url,
            revoke_certificate_url=revoke_certificate_url,
        )


class AcmeHeader(josepy.jws.Header):
    nonce = josepy.json_util.Field('nonce', omitempty=True)
    url = josepy.json_util.Field('url', omitempty=True)


class AcmeSignature(josepy.jws.Signature):
    header_cls = AcmeHeader
    __slots__ = ('combined',)


class AcmeJws(josepy.jws.JWS):
    signature_cls = AcmeSignature
    __slots__ = ('payload', 'signatures')
