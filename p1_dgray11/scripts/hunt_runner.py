#!/usr/bin/env python3
import math
import random
import rospy

from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtlesim.srv import Spawn, Kill

HUNTER_NAME = "turtle1"   #default turtlesim turtle
RUNNER_NAME = "runner"   #spawn/respawn with this name

CATCH_DISTANCE = 1.0

RUNNER_LINEAR = 1.0
RUNNER_ANG_MIN = -1.0
RUNNER_ANG_MAX = 1.0
RUNNER_ANG_UPDATE_SEC = 2.0

HUNTER_MAX_LINEAR = 1.0
K_LINEAR = 0.8     #proportional gain for forward speed
K_ANGULAR = 3.0    #proportional gain for turning

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def angle_wrap(a):
    """Wrap angle to [-pi, pi]."""
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a

class HunterRunnerNode:
    def __init__(self):
        self.hunter_pose = None
        self.runner_pose = None

        #Publishers
        self.hunter_pub = rospy.Publisher(f"/{HUNTER_NAME}/cmd_vel", Twist, queue_size=10)
        self.runner_pub = rospy.Publisher(f"/{RUNNER_NAME}/cmd_vel", Twist, queue_size=10)

        #Subscribers
        rospy.Subscriber(f"/{HUNTER_NAME}/pose", Pose, self._hunter_cb)
        rospy.Subscriber(f"/{RUNNER_NAME}/pose", Pose, self._runner_cb)

        #Services
        rospy.wait_for_service("/spawn")
        rospy.wait_for_service("/kill")
        self.spawn_srv = rospy.ServiceProxy("/spawn", Spawn)
        self.kill_srv = rospy.ServiceProxy("/kill", Kill)

        #Runner angular velocity state
        self.runner_ang = 0.0
        self._set_new_runner_ang(None)

        #Timer to update runner angular velocity every 2 seconds
        rospy.Timer(rospy.Duration(RUNNER_ANG_UPDATE_SEC), self._set_new_runner_ang)

        #Making sure we have a runner turtle
        self.ensure_runner_exists()

    def _hunter_cb(self, msg: Pose):
        self.hunter_pose = msg

    def _runner_cb(self, msg: Pose):
        self.runner_pose = msg

    def _set_new_runner_ang(self, _event):
        self.runner_ang = random.uniform(RUNNER_ANG_MIN, RUNNER_ANG_MAX)

    def ensure_runner_exists(self):
        """
        Spawn the runner named RUNNER_NAME.
        If it already exists, kill it first (safe reset), then respawn.
        """
        #Try killing existing runner, ignore errors
        try:
            self.kill_srv(RUNNER_NAME)
        except rospy.ServiceException:
            pass

        #Spawn at random position
        self.spawn_runner_random()

    def spawn_runner_random(self):
        #turtlesim world is roughly x,y in [0..11], keep margins
        x = random.uniform(1.0, 10.5)
        y = random.uniform(1.0, 10.5)
        theta = random.uniform(-math.pi, math.pi)

        try:
            self.spawn_srv(x, y, theta, RUNNER_NAME)
            rospy.loginfo(f"Spawned runner at x={x:.2f}, y={y:.2f}, theta={theta:.2f}")
        except rospy.ServiceException as e:
            rospy.logerr(f"Spawn failed: {e}")

    def publish_runner_cmd(self):
        cmd = Twist()
        cmd.linear.x = RUNNER_LINEAR
        cmd.angular.z = self.runner_ang
        self.runner_pub.publish(cmd)

    def publish_hunter_cmd(self):
        if self.hunter_pose is None or self.runner_pose is None:
            return

        dx = self.runner_pose.x - self.hunter_pose.x
        dy = self.runner_pose.y - self.hunter_pose.y
        dist = math.sqrt(dx*dx + dy*dy)

        #If close enough, catch runner: kill + respawn
        if dist < CATCH_DISTANCE:
            rospy.loginfo(f"Caught runner (dist={dist:.2f}). Killing + respawning.")
            try:
                self.kill_srv(RUNNER_NAME)
            except rospy.ServiceException:
                pass
            self.spawn_runner_random()
            #after respawn, runner_pose may be stale for a moment, just stop hunter briefly
            self.hunter_pub.publish(Twist())
            return

        target_theta = math.atan2(dy, dx)
        err = angle_wrap(target_theta - self.hunter_pose.theta)

        cmd = Twist()
        cmd.linear.x = clamp(K_LINEAR * dist, 0.0, HUNTER_MAX_LINEAR)
        cmd.angular.z = clamp(K_ANGULAR * err, -2.0, 2.0)
        self.hunter_pub.publish(cmd)

    def spin(self):
        rate = rospy.Rate(10)  #10 Hz control loop
        while not rospy.is_shutdown():
            self.publish_runner_cmd()
            self.publish_hunter_cmd()
            rate.sleep()

if __name__ == "__main__":
    rospy.init_node("hunter_runner")
    node = HunterRunnerNode()
    node.spin()



