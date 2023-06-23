import secrets
from pathlib import Path
from typing import List, Optional

import pytest

from tests.integration.dev_server import DevServer
from tests.integration.robot_client import RobotClient
from tests.integration.protocol_files import get_py_protocol


@pytest.mark.parametrize(
    ("num_to_configure_as_maximum", "num_to_upload", "num_to_expect"),
    [
        (None, 10, 5),  # Test that the server enforces a limit of 5 by default.
        (3, 6, 3),
    ],
)
async def test_protocols_auto_delete(
    num_to_configure_as_maximum: Optional[int],
    num_to_upload: int,
    num_to_expect: int,
    session_system_server_port: str,
) -> None:
    port = "15555"
    system_server_port = session_system_server_port
    async with RobotClient.make(
        base_url=f"http://localhost:{port}", version="*", system_server_base_url=f"http://localhost:{system_server_port}"
    ) as robot_client:
        assert (
            await robot_client.wait_until_dead()
        ), "Dev Robot is running and must not be."
        with DevServer(
            port=port,
            maximum_unused_protocols=num_to_configure_as_maximum,
            system_server_port=system_server_port,
        ) as server:
            server.start()
            assert (
                await robot_client.wait_until_alive()
            ), "Dev Robot never became available."

            await robot_client.get_auth_token()

            uploaded_protocol_ids = await _upload_protocols(
                robot_client=robot_client, num_protocols=num_to_upload
            )

            fetched_protocol_ids = await _get_protocol_ids(robot_client=robot_client)

            # Last n elements of uploaded_protocol_ids.
            protocol_ids_to_expect = uploaded_protocol_ids[-num_to_expect:]

            assert fetched_protocol_ids == protocol_ids_to_expect

            # Note that we don't cover more complicated cases here,
            # like making sure a protocol isn't deleted if there's a run
            # referring to it. These are covered by the unit tests for
            # `robot_server.deletion_planner`.


async def _upload_protocols(robot_client: RobotClient, num_protocols: int) -> List[str]:
    """Upload several protocols and return their IDs."""
    uploaded_protocol_ids: List[str] = []
    for _ in range(num_protocols):
        with get_py_protocol(secrets.token_urlsafe(16)) as file:
            response = await robot_client.post_protocol([Path(file.name)])
            uploaded_protocol_ids.append(response.json()["data"]["id"])
    return uploaded_protocol_ids


async def _get_protocol_ids(robot_client: RobotClient) -> List[str]:
    """Return the IDs of all protocols on the server."""
    response = await robot_client.get_protocols()
    return [p["id"] for p in response.json()["data"]]
