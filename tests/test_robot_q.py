#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2024-11-27
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#

import unittest
from pathlib import Path
from robomeshcat import Robot


class TestRobot(unittest.TestCase):
    def test_q_by_name(self):
        robot = Robot(urdf_path=Path(__file__).parent / 'test_urdf.urdf')

        robot["shoulder_pan_joint"] = 0.1
        self.assertAlmostEqual(robot["shoulder_pan_joint"], 0.1)
        self.assertAlmostEqual(robot[0], 0.1)


if __name__ == '__main__':
    unittest.main()
