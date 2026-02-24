#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import Twist
from std_srvs.srv import Empty
import math

def move(pub, lin, ang, duration):
    msg = Twist()
    msg.linear.x = lin
    msg.angular.z = ang
    rate = rospy.Rate(10)
    start = rospy.Time.now()
    while (rospy.Time.now() - start).to_sec() < duration:
        pub.publish(msg)
        rate.sleep()

def main():
    rospy.init_node('draw_DG')
    pub = rospy.Publisher('/turtle1/cmd_vel', Twist, queue_size=10)
    rospy.sleep(1.0)

    #Reset turtle
    rospy.wait_for_service('/reset')
    reset = rospy.ServiceProxy('/reset', Empty)
    reset()
    rospy.sleep(0.5)

    #Face up
    move(pub, 0, 1.0, math.pi/2)

    #Drawing D
    move(pub, 1.0, 0, 2.0)        #vertical line
    move(pub, 0, -1.0, math.pi/2) #turn
    move(pub, 0.5, 0, 1.0)  #added line
    move(pub, 1.0, -1.0, 3.0)     #curved side
    move(pub, 0.5, 0, 1.0)  #added line
    move(pub, 0, -1.0, math.pi/2) #turn

    #Move to G start
    move(pub, 0, -1.0, math.pi/2)  #added turn
    move(pub, 0.5, 0, 1.0)  #added line
    move(pub, 0, 1.0, math.pi/2)  #added turn
    move(pub, 0, -1.0, math.pi/2)
    move(pub, 0.5, 0.5, 3.0)
    move(pub, 0, -2.0, math.pi/2)

    #Drawing G
    move(pub, 1.0, 1.0, 3.0)
    move(pub, 0, 1.0, math.pi/2)
    move(pub, 0.5, 0, 1.0)
    move(pub, 0, 2.0, math.pi/2)
    move(pub, 0.5, 0, 1.0)
    move(pub, 0, -1.0, math.pi/2)
    move(pub, 1.0, -1.0, 3.0)
    move(pub, 1.0, -1.0, 1.0)

    rospy.loginfo("Finished drawing DG")

if __name__ == '__main__':
    main()
