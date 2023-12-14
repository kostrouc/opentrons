"""Pressure Overnight."""
import argparse
import asyncio
from time import time

from hardware_testing.opentrons_api import types
from hardware_testing.opentrons_api import helpers_ot3

TEST_POS = types.Point(x=221.72, y=161.33, z=93.51)


async def _main(is_simulating: bool, seconds: float) -> None:
    api = await helpers_ot3.build_async_ot3_hardware_api(
        is_simulating=is_simulating, pipette_left="p1000_single_v3.5"
    )
    mnt = types.OT3Mount.LEFT
    # await api.home()
    await api.add_tip(mnt, helpers_ot3.get_default_tip_length(50))
    # input("about to move up, press ENTER:")
    await api.move_rel(mnt, types.Point(z=10))
    await api.prepare_for_aspirate(mnt)
    await api.move_rel(mnt, types.Point(z=-10))
    start_time = time()
    count = 0
    while time() - start_time < seconds:
        count += 1
        print(f"cycles #{count}")
        await api.aspirate(mnt, 800)
        await api.dispense(mnt, push_out=0)
    print("done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--seconds", type=float, default=30.0)
    args = parser.parse_args()
    asyncio.run(_main(args.simulate, args.seconds))
