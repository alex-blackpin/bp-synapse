# Copyright 2020 Half-Shot
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from typing import TYPE_CHECKING, Tuple

from synapse.api.errors import Codes, SynapseError
from synapse.http.server import HttpServer
from synapse.http.servlet import RestServlet
from synapse.http.site import SynapseRequest
from synapse.types import JsonDict, UserID

from ._base import client_patterns

if TYPE_CHECKING:
    from synapse.server import HomeServer

logger = logging.getLogger(__name__)


class UserMutualRoomsServlet(RestServlet):
    """
    GET /uk.half-shot.msc2666/user/mutual_rooms/{user_id} HTTP/1.1
    """

    PATTERNS = client_patterns(
        "/uk.half-shot.msc2666/user/mutual_rooms/(?P<user_id>[^/]*)",
        releases=(),  # This is an unstable feature
    )

    def __init__(self, hs: "HomeServer"):
        super().__init__()
        self.auth = hs.get_auth()
        self.store = hs.get_datastores().main
        self.user_directory_search_enabled = (
            hs.config.userdirectory.user_directory_search_enabled
        )

    async def on_GET(
        self, request: SynapseRequest, user_id: str
    ) -> Tuple[int, JsonDict]:

        if not self.user_directory_search_enabled:
            raise SynapseError(
                code=400,
                msg="User directory searching is disabled. Cannot determine shared rooms.",
                errcode=Codes.UNKNOWN,
            )

        UserID.from_string(user_id)

        requester = await self.auth.get_user_by_req(request)
        if user_id == requester.user.to_string():
            raise SynapseError(
                code=400,
                msg="You cannot request a list of shared rooms with yourself",
                errcode=Codes.FORBIDDEN,
            )

        rooms = await self.store.get_mutual_rooms_for_users(
            requester.user.to_string(), user_id
        )

        return 200, {"joined": list(rooms)}


def register_servlets(hs: "HomeServer", http_server: HttpServer) -> None:
    UserMutualRoomsServlet(hs).register(http_server)
