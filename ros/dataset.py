import time
from typing import NamedTuple, List

from panda import Panda

from src import ansi

Z_DOWN = [0.0, 1.0, 0.0, 0.0]
HOME = [0.510, 0.0160, 0.090]


def format_time(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")

    return " ".join(parts)


class Point(NamedTuple):
    x: float
    y: float
    z: float

    def __repr__(self):
        return f"({self.x:.4f}, {self.y:.4f}, {self.z:.4f})"

    def __add__(self, other):
        return Point(self.x+other.x, self.y+other.y, self.z+other.z)

    def to_list(self) -> List[float]:
        return [self.x, self.y, self.z]


class CapData(NamedTuple):
    name: str
    center_pos: Point


def run() -> None:
    panda = Panda(rate=10)
    panda.start("giovanni")

    caps = [
        # CapData(name="s_110", center_pos=Point(0.5100, 0.0160, 0.0710)),
        CapData(name="skin", center_pos=Point(0.5100, 0.0160, 0.068)),
        # CapData(name="s_coin", center_pos=Point(0.5100, 0.0160, 0.0710)),
        # CapData(name="m_110", center_pos=Point(0.5100, 0.0160, 0.0795)),
        # CapData(name="l_110", center_pos=Point(0.5100, 0.0160, 0.083)),
    ]

    # loops
    offset = 0.0050
    z_offset = 0.0012
    positions = {
        "center": Point(0.0, 0.0, z_offset),
        "upper_left": Point(offset, offset, z_offset),
        "upper_right": Point(offset, -offset, z_offset),
        "lower_left": Point(-offset, offset, z_offset),
        "lower_right": Point(-offset, -offset, z_offset),
    }

    forces = {
        # "0.5": -0.0030,
        "1.0": -0.0035,
        # "1.0": -0.0037,
        # "1.5": -0.0042,
        # "2.0": -0.0050,
        # "2.5": -0.0060,
        # "3.0": -0.0067,
    }

    # experiments
    n_touchs = 2
    touching_time = 10
    resting_time = 10

    for position, start_offset in positions.items():
        start = caps[0].center_pos + start_offset

        # initial approximation to surface
        panda.go_to_pose(
            position=start.to_list(),
            orientation=Z_DOWN,
            duration=0.5,
        )
        time.sleep(0.5)

        for force, z_offset in forces.items():
            print(f"-> touching {position} with force {force}")
            goal = Point(start.x, start.y, start.z+z_offset)

            for i in range(n_touchs):
                print(f"touching {i+1}")

                # press
                panda.go_to_pose(
                    position=goal.to_list(),
                    orientation=Z_DOWN,
                    duration=0.5,
                )
                time.sleep(touching_time)

                # release
                panda.go_to_pose(
                    position=start.to_list(),
                    orientation=Z_DOWN,
                    duration=0.25,
                )
                time.sleep(resting_time)

        # return home
        panda.go_to_pose(
            position=HOME,
            orientation=Z_DOWN,
            duration=0.5,
        )

        # take time to stop and start measurements
        # answer = input("continue? [y],n: ")
        # if answer == "n":
        #     return


def dataset():
    panda = Panda(rate=10)
    panda.start("giovanni")

    # furniture pad
    # center = Point(0.5100, 0.0160, 0.0680)
    # force_offsets = {
    #     # "0.5N": -0.0021,
    #     # "1.0N": -0.0023,
    #     "1.5N": -0.0025,
    #     # "2.0N": -0.0028,
    #     # "2.5N": -0.0031,
    #     # "3.0N": -0.0034,
    #     # "3.5N": -0.0037,
    #     # "4.0N": -0.0040,
    # }

    # squishy cap
    center = Point(0.5100, 0.0160, 0.076)
    force_offsets = {
        # "0.5N": -0.0030,
        # "1.0N": -0.0045,
        "1.5N": -0.0065,
        # "2.0N": -0.0080,
        # "2.5N": -0.0090,
        # "3.0N": -0.0100,
        # "3.5N": -0.0105,
        # "4.0N": -0.0110,
    }

    z_offset = 0.0015
    max_radius = 0.0060
    radius_offsets = {
        # "25%": max_radius*0.25,
        "50%": max_radius*0.5,
        # "75%": max_radius*0.75,
        # "100%": max_radius*1.0,
    }

    # variables
    n_touchs = 1
    touching_time = 1
    resting_time = 1
    press_duration = 0.75
    release_duration = 0.25

    counter = 0
    start_time = time.time()

    for radius_idx, (radius_tag, radius_offset) in enumerate(radius_offsets.items()):
        positions = {
            "center": Point(0.0, 0.0, z_offset),
            "right": Point(0.0, -radius_offset, z_offset),
            "up_right": Point(radius_offset, -radius_offset, z_offset),
            "up": Point(radius_offset, 0.0, z_offset),
            "up_left": Point(radius_offset, radius_offset, z_offset),
            "left": Point(0.0, radius_offset, z_offset),
            "down_left": Point(-radius_offset, radius_offset, z_offset),
            "down": Point(-radius_offset, 0.0, z_offset),
            "down_right": Point(-radius_offset, -radius_offset, z_offset),
        }

        for position_idx, (position_tag, position_offset) in enumerate(positions.items()):
            for force_idx, (force_tag, force_offset) in enumerate(force_offsets.items()):
                start = center + position_offset
                goal = Point(start.x, start.y, start.z+force_offset)

                # initial approximation to surface
                if force_idx == 0:
                    panda.go_to_pose(
                        position=start.to_list(),
                        orientation=Z_DOWN,
                        duration=0.5,
                    )
                    time.sleep(resting_time)

                for touch_idx in range(n_touchs):
                    counter += 1
                    n_positions = len(positions)
                    n_forces = len(force_offsets)
                    n_radii = len(radius_offsets)
                    progress = int(counter/(n_positions*n_radii*n_forces*n_touchs)*100)
                    elapsed = int(time.time() - start_time)
                    remaining = int((1-progress/100) * elapsed)
                    print(
                        f"{ansi.CLEAR_SCREEN}{ansi.HOME}{ansi.GREEN}{ansi.BOLD}-> moving robot{ansi.RESET}",
                        f"   |> touch:     {touch_idx+1} out of {n_touchs}",
                        f"   |> position:  {position_tag} ({position_idx+1} out of {n_positions})",
                        f"   |> force:     {force_tag} ({force_idx+1} out of {n_forces})",
                        f"   |> radius:    {radius_tag} ({radius_idx+1} out of {n_radii})",
                        f"   |> progress:  {progress}%",
                        f"   |> elapsed:   {format_time(elapsed)}",
                        f"   |> remaining: {format_time(remaining)}",
                        sep="\n",
                    )

                    # press
                    panda.go_to_pose(
                        position=goal.to_list(),
                        orientation=Z_DOWN,
                        duration=press_duration,
                    )
                    time.sleep(touching_time)

                    # release
                    panda.go_to_pose(
                        position=start.to_list(),
                        orientation=Z_DOWN,
                        duration=release_duration,
                    )
                    time.sleep(resting_time)

                # end touchs -> next force

            # end forces -> next position
            # panda.go_to_pose(
            #     position=HOME,
            #     orientation=Z_DOWN,
            #     duration=0.5,
            # )

            # answer = input("continue? [y/n]: ")
            # if answer == "n":
            #     return

        # end positions -> next radius
        panda.go_to_pose(
            position=HOME,
            orientation=Z_DOWN,
            duration=0.5,
        )

    # end radii -> finish


if __name__ == "__main__":
    # run()
    dataset()
