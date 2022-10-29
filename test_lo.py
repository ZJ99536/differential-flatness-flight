#!/usr/bin/env python
import rospy
from geometry_msgs.msg import *
from mavros_msgs.msg import *
from mavros_msgs.srv import *
from tf.transformations import euler_from_quaternion
import time
from std_msgs.msg import Float32


class Logger:
    def __init__(self):
        self.f = open("/home/nesc/Desktop/test01.txt", 'w')
        self.local_pos = [str(0),str(0),str(0)]
        self.target_pos = [str(0),str(0),str(0)]
        self.local_vel = [str(0),str(0),str(0)]
        self.target_vel = [str(0),str(0),str(0)]
        self.local_att = [str(0),str(0),str(0)]
        self.target_att = [str(0),str(0),str(0)]
        self.local_bodyrate = [str(0),str(0),str(0)]
        self.target_bodyrate = [str(0),str(0),str(0)]
        self.count = 0
        self.current_time = Float32()
        self.current_time.data = .0
        self.start_time = 0 
        self.cur_time = 0
        rospy.Subscriber("/mavros/local_position/pose", PoseStamped,self.poseCb)
        rospy.Subscriber("/mavros/local_position/velocity_local",TwistStamped,self.velCb)
        # rospy.Subscriber("/mavros/setpoint_raw/target_local", PositionTarget,self.tarposCb)
        rospy.Subscriber("/mavgnc/position_setpoint", PoseStamped, self.tarposCb)
        rospy.Subscriber("/mavgnc/velocity_setpoint",TwistStamped, self.tarvelCb
)
        rospy.Subscriber("/mavgnc/att_sp_euler", Vector3Stamped, self.tarattCb)
        rospy.Subscriber("/mavgnc/att_euler", Vector3Stamped, self.attCb)
        rospy.Subscriber("/mavros/setpoint_raw/attitude", AttitudeTarget,self.tarpqrCb)

    def write_data(self):
        if self.count != 0:
            self.cur_time = time.perf_counter()
            self.f.write(str(self.cur_time-self.start_time))
            # self.f.write(str(self.current_time.data))
            self.f.write(',')
            self.f.write(','.join(self.local_pos))
            self.f.write(',')
            self.f.write(','.join(self.target_pos))
            self.f.write(',')
            self.f.write(','.join(self.local_vel))
            self.f.write(',')
            self.f.write(','.join(self.target_vel))
            self.f.write(',')
            self.f.write(','.join(self.local_att))
            self.f.write(',')
            self.f.write(','.join(self.target_att))
            self.f.write(',')
            self.f.write(','.join(self.local_bodyrate))
            self.f.write(',')
            self.f.write(','.join(self.target_bodyrate))
            self.f.write('\r\n')
        self.count += 1

    def write_title(self):
        self.f.write("x,y,z,target_x,target_y,target_z,vel_x,vel_y,vel_z,target_vel_x,target_vel_y,target_vel_z,att_x,att_y,att_z,target_att_x,target_att_y,target_att_z,rate_x,rate_y,rate_z,target_rate_x,target_rate_y,target_rate_z")
        self.f.write('\r\n')

    def poseCb(self,msg):
        self.local_pos = [str(msg.pose.position.x), str(msg.pose.position.y), str(msg.pose.position.z)]
        # quaternion = [msg.pose.orientation.x,msg.pose.orientation.y,msg.pose.orientation.z,msg.pose.orientation.w]
        # self.local_att = euler_from_quaternion(quaternion)
        # self.local_att = list(map(str,self.local_att))
     
    def attCb(self, msg):
        self.local_att = [str(msg.vector.x), str(msg.vector.y), str(msg.vector.z)]
    
    def tarvelCb(self, msg):
        self.target_vel = [str(msg.twist.linear.x), str(msg.twist.linear.y), str(msg.twist.linear.z)]

    def tarposCb(self,msg):
        self.target_pos = [str(msg.pose.position.x), str(msg.pose.position.y), str(msg.pose.position.z)]
        # self.target_vel = [str(msg.velocity.x), str(msg.velocity.y), str(msg.velocity.z)]
        # self.target_vel = [str(self.Kp1x*(float(self.target_pos[0])-float(self.local_pos[0]))), str(self.Kp1y*(float(self.target_pos[1])-float(self.local_pos[1]))), str(self.Kp1z*(float(self.target_pos[2])-float(self.local_pos[2])))]
        # rospy.loginfo("target_vel:", self.target_vel[0])

    def velCb(self, msg):
        self.local_vel = [str(msg.twist.linear.x), str(msg.twist.linear.y), str(msg.twist.linear.z)]

    def tarattCb(self, msg):
        self.target_att = [str(msg.vector.x), str(msg.vector.y), str(msg.vector.z)]
        # self.target_att = euler_from_quaternion(quaternion)
        # self.target_att = list(map(str, self.target_att))

    def tarpqrCb(self,msg):
        # quaternion = [msg.orientation.x,msg.orientation.y,msg.orientation.z,msg.orientation.w]
        # self.target_att = euler_from_quaternion(quaternion)
        # self.target_att = list(map(str,self.target_att))
        self.target_bodyrate = [str(msg.body_rate.x), str(msg.body_rate.y), str(msg.body_rate.z)]
        
def main():
    print("start log!")
    rospy.init_node('logger_node', anonymous=True)
    logger = Logger()
    logger.write_title()
    rate = rospy.Rate(2)
    logger.start_time = time.perf_counter()

    while not rospy.is_shutdown():
        logger.write_data()
        rate.sleep()
    logger.f.close()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
