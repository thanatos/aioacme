from typing import List, Tuple
from yarl import URL

from . import authorization
from . import order as _order
from . import util


class Account:
    def __init__(
            self,
            client: 'aioacme.AcmeClient',
            private_key,
            account_href: str,
    ) -> None:
        """A reference to an account on an ACME server.

        If you know the URL that corresponds to your account, you can create
        this object directly.

        If you do not know the URL, you can call ``existing_account_from_key``
        on a ``Client`` object, which will return an ``Account``. (After which,
        you can store the ``account_href`` if you wish to create the
        ``Account`` object again.)
        """
        self.client = client
        self.private_key = private_key
        self.account_href = account_href

    async def new_order(
            self, identifiers,
    ) -> Tuple[URL, _order.Order, List[Tuple[URL, authorization.Authorization]]]:
        json_data = {
            'identifiers': [
                identifier.to_json() for identifier in identifiers
            ],
        }

        response_status, response_headers, response_json = \
            await self._post_json_with_key_id(
                self.client.directory.new_order_url,
                json_data,
            )

        order_href = URL(response_headers['Location'])

        order = _order.Order.from_json(response_json)

        authorizations = []
        for authorization_url in order.authorization_urls:
            auth_json = await self.client._get(str(authorization_url))
            authorizations.append((
                authorization_url,
                authorization.authorization_from_json(auth_json),
            ))

        return order_href, order, authorizations

    async def begin_http_01_challenge(self, challenge):
        return await self._post_with_key_id(str(challenge.url), b'{}')

    async def finalize_order(self, finalize_order_url, csr_data: bytes):
        """Finalize an order by uploading a CSR to be signed.

        :param csr_data:
            The CSR to sign; this should be an X.509 CSR in DER format.
        """
        response_status, response_headers, response_json = \
            await self._post_json_with_key_id(
                str(finalize_order_url),
                {'csr': util.acme_b64encode(csr_data)},
            )

        return _order.Order.from_json(response_json)

    async def _post_with_key_id(self, url, data):
        return await self.client._post_with_key_id(
            url,
            data,
            self.private_key,
            self.account_href,
        )

    async def _post_json_with_key_id(self, url, json_data):
        return await self.client._post_json_with_key_id(
            url,
            json_data,
            self.private_key,
            self.account_href,
        )
