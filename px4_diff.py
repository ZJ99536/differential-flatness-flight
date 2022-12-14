import rospy
from geometry_msgs.msg import PoseStamped, Quaternion, Vector3,TwistStamped,Vector3Stamped
from mavros_msgs.msg import *
from mavros_msgs.srv import *
from scipy.spatial.transform import Rotation as R
import threading
import matplotlib.pyplot as plt
from time import time
import math
from math import sin,cos,tan,atan,asin,acos,atan2
import numpy as np
from nav_msgs.msg import Odometry 
from std_msgs.msg import Float32, Header
from tf.transformations import quaternion_from_euler,euler_from_quaternion,quaternion_from_matrix

def quaternion2euler(quaternion):
    r = R.from_quat(quaternion)
    euler = r.as_euler('xyz', degrees=True)
    return euler

def thread_job():
    rospy.spin()

class Controller:
    
    def __init__(self):        
        # current state 
        self.state = State()
        # vision pos
        self.vision_pos = PoseStamped()
        # local pos as reference
        self.ref_pos = PoseStamped()

        self.att = AttitudeTarget() 
        self.position_setpoint = PoseStamped() 
        self.velocity_setpoint = TwistStamped() 
        self.att_setpoint_euler = Vector3Stamped()
        self.attitude_euler = Vector3Stamped()

        self.current_position = np.zeros(3)
        self.current_velocity= np.zeros(3)
        self.current_attitude = np.zeros(3)

        self.hp = np.array((3,))
        self.status = 'Hover'
        self.flag = 0

        self.att_setpoint_pub = rospy.Publisher('mavros/setpoint_raw/attitude', AttitudeTarget, queue_size=1)
        self.vel_setpoint_pub = rospy.Publisher('mavgnc/velocity_setpoint', TwistStamped, queue_size=1)
        self.pos_setpoint_pub = rospy.Publisher('mavgnc/position_setpoint', PoseStamped, queue_size=1)
        self.att_sp_euler_pub = rospy.Publisher('mavgnc/att_sp_euler',Vector3Stamped,queue_size=1)
        self.att_euler_pub = rospy.Publisher('mavgnc/att_euler',Vector3Stamped,queue_size=1)
        
        # self.odom_sub = rospy.Subscriber('mavros/local_position/odom',Odometry,self.odometry_cb)

        self.vision_pub = rospy.Publisher("/mavros/vision_pose/pose",PoseStamped, queue_size = 1)
        


        
        self.phi_cmd = 0.0
        self.theta_cmd = 0.0
        self.psi_cmd = 0.0
        self.thrust_cmd = 0.0


        self.kp_x = 0.35
        self.kp_y = 0.35
        self.kp_z = 0.2

        self.kp_vx = 0.3
        self.kp_vy = -0.3
        self.kp_vz = 0.5

        self.ki_x = 0
        self.ki_y = 0
        self.ki_z = 0.01
        self.ki_x_fb = 0
        self.ki_y_fb = 0
        self.ki_z_fb = 0.01

        self.kd_x = 0
        self.kd_y = 0
        self.kd_z = 0

        self.ki_vx = 0
        self.ki_vy = 0
        self.ki_vz = 0.02
        self.ki_vz_fb = 0.02

        self.kd_vx = 0
        self.kd_vy = 0
        self.kd_vz = 0

        self.vel_err_sum = np.zeros(3)
        self.vel_err_last_step = np.zeros(3)
        self.pos_err_sum = np.zeros(3)
        self.pos_err_last_step = np.zeros(3)

 
        self.ts = 0
        self.tss = None
        self.tsa = None
        self.n_seg = 0
        self.n_order = 7
        self.Q = None
        self.M = None
        self.C = None
        self.Rp = None
        self.Rpp = None
        self.Rfp = None
        self.polyx = None
        self.polyy = None
        self.polyz = None
        self.tempi = 0
        self.endx = 0
        self.endy = 0
        self.endz = 0

        self.cut_seg = 10
        self.eight_turns = 5
        self.eight_ax = 2
        self.eight_ay = 3
        self.eight_t = 2*np.pi/self.cut_seg
        self.start_t = 0
        self.current_t = 0

        self.g = 9.81
        self.k_p_fb = 1.3
        self.k_v_fb = 3.5
        self.k_p_att_euler = [5, 5, 5]

        self.vxmax = 1.2
        self.vymax = 1.1
        self.vzmax = 1.1

        # self.add_thread = threading.Thread(target = self.thread_job)
        # self.add_thread.start()
        
        # self.att_thread = Thread(target=self.send_att, args=())
        # self.att_thread.daemon = True
        # self.att_thread.start()

       
        self.loop_freq = 100
        self.loop_rate = rospy.Rate(self.loop_freq)

        self.time_init = time()
        self.current_time = Float32()
        self.current_time.data = .0

       

    # ????????????
    # ??????????????????
    def posCb(self, msg):
        self.vision_pos = msg
        quaternion = [msg.pose.orientation.x,msg.pose.orientation.y,msg.pose.orientation.z,msg.pose.orientation.w]
        euler = euler_from_quaternion(quaternion)
        self.vision_pos.header.stamp = rospy.Time.now()
        self.vision_pub.publish(self.vision_pos)
        self.current_position = np.array([self.vision_pos.pose.position.x,self.vision_pos.pose.position.y,self.vision_pos.pose.position.z])
        self.current_attitude = np.array(euler)
        # self.send_att()
        # print("optitrack_pos:" , self.local_pos.pose.position.x,self.local_pos.pose.position.y,self.local_pos.pose.position.z)
        # print("optitrack_pose:",euler)

    def stateCb(self, msg):
        self.state = msg
        print("current mode is: ",self.state.mode)

    def refCb(self, msg):
        self.cur_pos = msg
        quaternion = [msg.pose.orientation.x,msg.pose.orientation.y,msg.pose.orientation.z,msg.pose.orientation.w]
        euler = quaternion2euler(quaternion)
        # self.current_attitude = np.array(euler)
        # print("current_pos: " , self.cur_pos.pose.position.x,self.cur_pos.pose.position.y,self.cur_pos.pose.position.z)
        # print("current_pose: ", euler)
        
    def vrefCb(self, msg):
        self.current_velocity = np.array([msg.twist.linear.x, msg.twist.linear.y, msg.linear.z])

    def send_att(self):
        self.att.header = Header()
        self.att.header.frame_id = "base_footprint"
        self.att.header.stamp = rospy.Time.now()
        self.att_setpoint_pub.publish(self.att)
        self.vel_setpoint_pub.publish(self.velocity_setpoint)
        self.pos_setpoint_pub.publish(self.position_setpoint)
        self.att_euler_pub.publish(self.attitude_euler)
        self.att_sp_euler_pub.publish(self.att_setpoint_euler)
   
    def is_at_setpoint(self):
        self.position_setpoint.pose.position.x = 0
        self.position_setpoint.pose.position.y = 0
        self.position_setpoint.pose.position.z = 1

        self.hp = np.array([self.position_setpoint.pose.position.x, self.position_setpoint.pose.position.y, self.position_setpoint.pose.position.z])
        dis = self.current_position - self.hp

        if np.linalg.norm(dis) < 0.1:
            self.status = 'Planning'
        else:
            self.status = 'Hover'
        

    def position_control_fb(self):
        position_cmd = np.array([self.position_setpoint.pose.position.x,self.position_setpoint.pose.position.y,self.position_setpoint.pose.position.z])
        pos_err = position_cmd - self.current_position
        self.pos_err_sum += pos_err * 1.0/self.loop_freq
        
        if self.state.mode == "OFFBOARD":
            self.pos_err_sum += pos_err * 1.0/self.loop_freq
        else:
            self.pos_err_sum = np.zeros(3)

        self.velocity_setpoint.twist.linear.x = self.kp_x * pos_err[0]
        self.velocity_setpoint.twist.linear.y = self.kp_y * pos_err[1]
        self.velocity_setpoint.twist.linear.z = self.kp_z * pos_err[2] + self.ki_z_fb * self.pos_err_sum[2]
        self.position_setpoint.header.stamp = rospy.Time.now() 
        self.position_setpoint.header.frame_id = 'odom'
        self.velocity_setpoint.header.stamp = rospy.Time.now()  
        self.velocity_setpoint.header.frame_id = 'odom'

        self.psi_cmd = 0.0

    def velocity_control_fb(self):
        velocity_cmd = np.array([self.velocity_setpoint.twist.linear.x,self.velocity_setpoint.twist.linear.y,self.velocity_setpoint.twist.linear.z])
        vel_err = velocity_cmd - self.current_velocity

        psi = self.current_attitude[2]
        
        R_E_B = np.array([[cos(psi),sin(psi),0],[-sin(psi),cos(psi),0],[0,0,1]])
        vel_err = R_E_B@vel_err

        if self.state.mode == "OFFBOARD":
            self.vel_err_sum += vel_err * 1.0/self.loop_freq
        else:
            self.vel_err_sum = np.zeros(3)
        
        print("vel_error_sum")
        print(self.vel_err_sum)
        
        self.thrust_cmd = 0.27 + self.kp_vz * vel_err[2] + self.ki_vz_fb * self.vel_err_sum[2]
        if self.thrust_cmd >= 1:
            self.thrust_cmd = 0.99
        elif self.thrust_cmd <= 0:
            self.thrust_cmd = 0.01
        print("thrust")
        print(self.thrust_cmd)
        self.theta_cmd = self.kp_vx * vel_err[0]
        self.phi_cmd = self.kp_vy * vel_err[1]
        
        self.att.orientation = Quaternion(*quaternion_from_euler(self.phi_cmd,self.theta_cmd,self.psi_cmd))
        self.att.thrust = self.thrust_cmd
        self.att.body_rate = Vector3()
        self.att.type_mask = 7 # ignore rate

        self.att_setpoint_euler.vector.x = self.phi_cmd/3.14*180
        self.att_setpoint_euler.vector.y = self.theta_cmd/3.14*180
        self.att_setpoint_euler.vector.z = self.psi_cmd/3.14*180
        self.att_setpoint_euler.header.stamp = rospy.Time.now()

        self.attitude_euler.vector.x = self.current_attitude[0]/3.14*180
        self.attitude_euler.vector.y = self.current_attitude[1]/3.14*180
        self.attitude_euler.vector.z = self.current_attitude[2]/3.14*180
        self.attitude_euler.header.stamp = rospy.Time.now()

        self.vel_err_last_step = vel_err


    def velocity_control(self):
        position_cmd = np.array([self.position_setpoint.pose.position.x,self.position_setpoint.pose.position.y,self.position_setpoint.pose.position.z])
        pos_err = position_cmd - self.current_position
        self.pos_err_sum += pos_err * 1.0/self.loop_freq
        velocity_cmd = np.array([self.velocity_setpoint.twist.linear.x,self.velocity_setpoint.twist.linear.y,self.velocity_setpoint.twist.linear.z])
        vel_err = velocity_cmd - self.current_velocity
        self.vel_err_sum += vel_err * 1.0/self.loop_freq
        ts = self.ts
        ta = np.array([42*ts**5, 30*ts**4, 20*ts**3, 12*ts**2, 6*ts, 2, 0, 0])
        aref = np.zeros(3)
        aref[0] = np.dot(ta, self.ax)
        aref[1] = np.dot(ta, self.ay)
        aref[2] = np.dot(ta, self.az)
        #print(error)
        # print(aref)
        phi = self.current_attitude[0]
        theta = self.current_attitude[1]
        psi = 0
        R_E_B = np.array([[cos(psi),sin(psi),0],[-sin(psi),cos(psi),0],[0,0,1]])
        # vel_err = R_E_B@vel_err
        K_pos = np.array([[self.k_p_fb,0,0],[0,self.k_p_fb,0],[0,0,self.k_p_fb]])
        K_vel = np.array([[2,0,0],[0,2,0],[0,0,2]])
        ades = aref + self.g*np.array([0,0,1]) + K_pos @ pos_err + K_vel @ vel_err
                              
        acc_des = ades
        # acc_des[0] += self.ki_vx * self.vel_err_sum[0] + self.kd_vx * (vel_err[0] - self.vel_err_last_step[0])*self.loop_freq
        # acc_des[0] += self.ki_x * self.pos_err_sum[0] + self.kd_x * (pos_err[0] - self.pos_err_last_step[0])*self.loop_freq
        # acc_des[1] += self.ki_y * self.pos_err_sum[1] + self.kd_y * (pos_err[1] - self.pos_err_last_step[1])*self.loop_freq
        # acc_des[2] += self.ki_vz * self.vel_err_sum[2] + self.kd_vz * (vel_err[2] - self.vel_err_last_step[2])*self.loop_freq
        # acc_des[2] += self.ki_z * self.pos_err_sum[2] + self.kd_z * (pos_err[2] - self.pos_err_last_step[2])*self.loop_freq
        acc_des[2] += self.ki_vz * self.vel_err_sum[2]
        acc_des[2] += self.ki_z * self.pos_err_sum[2]
        z_b_des = np.array(acc_des / np.linalg.norm(acc_des))
        y_c = np.array([-sin(psi),cos(psi),0])
        x_b_des = np.cross(y_c,z_b_des) / np.linalg.norm(np.cross(y_c,z_b_des))
        y_b_des = np.cross(z_b_des,x_b_des)
        
        # R_E_B = np.array([x_b_des,y_b_des,z_b_des])
        # self.att.orientation = Quaternion(*quaternion_from_matrix(R_E_B))
        R_E_B = np.transpose(np.array([x_b_des,y_b_des,z_b_des]))

        self.psi_cmd = atan2(R_E_B[1,0],R_E_B[0,0])
        self.theta_cmd = asin(-R_E_B[2,0])
        self.phi_cmd = atan(R_E_B[2,1]/R_E_B[2,2])
        self.thrust_cmd = np.linalg.norm(acc_des)*0.3/self.g

          
        # self.thrust_cmd = (np.dot(acc_des, z_b_des) + self.ki_vz * self.vel_err_sum[2] + self.kd_vz * (vel_err[2] - self.vel_err_last_step[2])*self.loop_freq)*0.68/self.g      
        # self.thrust_cmd = 0.68 + self.kp_vz * vel_err[2] + self.ki_vz * self.vel_err_sum[2] + self.kd_vz * (vel_err[2] - self.vel_err_last_step[2])*self.loop_freq
        
        # self.theta_cmd += self.kd_vx * (vel_err[0] - self.vel_err_last_step[0])*self.loop_freq
        # self.phi_cmd += self.kd_vy * (vel_err[1] - self.vel_err_last_step[1])*self.loop_freq

        self.theta_cmd = self.bound(self.theta_cmd,-0.42,0.42)
        self.phi_cmd = self.bound(self.phi_cmd,-0.62,0.62)
        self.thrust_cmd = self.bound(self.thrust_cmd,0,0.9)

        print("thrust")
        print(self.thrust_cmd)

        psi = 0
        yc = np.array([-sin(psi),cos(psi),0])
        tj = np.array([210*ts**4, 120*ts**3, 60*ts**2, 24*ts, 6, 0, 0, 0])
        xj = np.dot(tj, self.ax)
        yj = np.dot(tj, self.ay)
        zj = np.dot(tj, self.az)
        j = np.zeros(3)
        j[0] = xj
        j[1] = yj
        j[2] = zj
        alpha = aref + self.g*np.array([0,0,1])
        xb = np.cross(yc,alpha)
        # print(xb)
        xb = xb / np.linalg.norm(xb)
        yb = np.cross(alpha,xb)
        yb = yb / np.linalg.norm(yb)
        zb = np.cross(xb, yb)
        c = np.dot(zb, alpha)
        w = np.zeros(3)
        w[0] = -np.dot(yb,j)/c
        w[1] = np.dot(xb,j)/c
        w[2] = w[1]*np.dot(yc,zb)/np.linalg.norm(np.cross(yc,zb))
        att_cmd = np.array([self.phi_cmd,self.theta_cmd,self.psi_cmd])
        w_fb = self.k_p_att_euler * (att_cmd - self.current_attitude)
        w_cmd = w + w_fb
        self.att.orientation = Quaternion(*quaternion_from_euler(self.phi_cmd,self.theta_cmd,self.psi_cmd))
        self.att.thrust = self.thrust_cmd
        self.att.body_rate.x = w_cmd[0]
        self.att.body_rate.y = w_cmd[1]
        self.att.body_rate.z = w_cmd[2]
        self.att.type_mask = 128 # ignore rate
        self.att.header.stamp = rospy.Time.now()

        self.att_setpoint_euler.vector.x = self.phi_cmd/3.14*180
        self.att_setpoint_euler.vector.y = self.theta_cmd/3.14*180
        self.att_setpoint_euler.vector.z = self.psi_cmd/3.14*180
        self.att_setpoint_euler.header.stamp = rospy.Time.now()

        self.attitude_euler.vector.x = self.current_attitude[0]/3.14*180
        self.attitude_euler.vector.y = self.current_attitude[1]/3.14*180
        self.attitude_euler.vector.z = self.current_attitude[2]/3.14*180
        self.attitude_euler.header.stamp = rospy.Time.now()

        self.vel_err_last_step = vel_err



    def position_control(self):
        # position_cmd = np.array([self.position_setpoint.pose.position.x,self.position_setpoint.pose.position.y,self.position_setpoint.pose.position.z])
        # pos_err = position_cmd - self.current_position
        # print(self.current_position)
        ts = self.ts
        tv = np.array([7*ts**6, 6*ts**5, 5*ts**4, 4*ts**3, 3*ts**2, 2*ts, 1, 0])
        self.velocity_setpoint.twist.linear.x = np.dot(tv, self.ax)
        self.velocity_setpoint.twist.linear.y = np.dot(tv, self.ay)
        self.velocity_setpoint.twist.linear.z = np.dot(tv, self.az)

        self.velocity_setpoint.header.stamp = rospy.Time.now()  
        self.velocity_setpoint.header.frame_id = 'odom'

        self.psi_cmd = 0.0

    def bound(self,data,min_value,max_value):
        if data >=max_value:
            data = max_value
        elif data <=min_value:
            data = min_value
        return data

    def planner(self):
        curren_t = self.current_t
        # print(curren_t)
        if self.tempi < len(self.tsa)-1 and curren_t > self.tsa[self.tempi+1]:
            self.tempi = self.tempi + 1
        self.ax = np.zeros(8)
        self.ay = np.zeros(8)
        self.az = np.zeros(8)            
        if self.tempi < len(self.tsa)-1:
            if self.tempi == 0:
                for i in range(5):
                    # print(i)
                    self.ax[i+3] = self.polyx[i]
                    self.ay[i+3] = self.polyy[i]
                    self.az[i+3] = self.polyz[i]
            elif self.tempi == len(self.tsa)-2:
                for i in range(5):
                    self.ax[i+3] = self.polyx[i-5]
                    self.ay[i+3] = self.polyy[i-5]
                    self.az[i+3] = self.polyz[i-5]
            else:
                for i in range(4):
                    self.ax[i+4] = self.polyx[self.tempi*4+1+i]
                    self.ay[i+4] = self.polyy[self.tempi*4+1+i]
                    self.az[i+4] = self.polyz[self.tempi*4+1+i]
        else:
            self.ax = np.array([0,0,0,0,0,0,0,self.endx])
            self.ay = np.array([0,0,0,0,0,0,0,self.endy])
            self.az = np.array([0,0,0,0,0,0,0,self.endz])

        self.ts = curren_t - self.tsa[self.tempi]
        ts = self.ts
        t = np.array([ts**7, ts**6, ts**5, ts**4, ts**3, ts**2, ts, 1])
        self.position_setpoint.pose.position.x = np.dot(t, self.ax)
        self.position_setpoint.pose.position.y = np.dot(t, self.ay)
        self.position_setpoint.pose.position.z = np.dot(t, self.az)

        self.position_setpoint.header.stamp = rospy.Time.now() 
        self.position_setpoint.header.frame_id = 'odom'


    def plan(self, waypointx, waypointy, waypointz):
        self.endx = waypointx[-1]
        self.endy = waypointy[-1]
        self.endz = waypointz[-1]
        # print(self.endx, self.endy, self.endz)
        self.n_seg = len(waypointx)-1
        # print(self.n_seg)
        self.init_ts(waypointx, waypointy, waypointz)     
        
        self.polyx = self.trajPlanning(self.tss, waypointx) 
        self.polyy = self.trajPlanning(self.tss, waypointy)
        self.polyz = self.trajPlanning(self.tss, waypointz)

        # print(self.polyx.shape)


    def init_ts(self, waypointx, waypointy, waypointz):
        # to be ++++++++++++++++++
        self.tss = np.ones(self.n_seg) * 10      
        # for i in range(1,len(self.tss)):
        #     t1 = abs(waypointx[i+1]-waypointx[i]) / self.vxmax
        #     t2 = abs(waypointy[i+1]-waypointy[i]) / self.vymax
        #     t3 = abs(waypointz[i+1]-waypointz[i]) / self.vzmax
        #     self.tss[i] = max(t1,max(t2,t3))
        # self.tss[0] = 10
        self.tsa = np.zeros(self.n_seg+1)
        for i in range(1, len(self.tsa)):
            self.tsa[i] = self.tsa[i-1] + self.tss[i-1]

    def trajPlanning(self, t, p):
        xMatrix = np.zeros((4*len(t)+2,1))
        for i in range(len(p)-1):
            xMatrix[i,0] = p[i]
            xMatrix[len(t)+i,0] = p[i+1]

        tMatrix = np.zeros((4*len(t)+2,4*len(t)+2)) 
        tMatrix[0,4] = 1 #p0(0)
        tMatrix[len(t)-1,-1] = 1 #pn(0)
        for j in range(5):
            tMatrix[len(t),j] = t[0]**(4-j) #p0(t)
            tMatrix[2*len(t)-1,-1-j] = t[-1]**j #pn(t)
        for i in range(1,len(t)-1):
            tMatrix[i,4*(i+1)] = 1 #pi(0)
            for j in range(4):
                tMatrix[len(t)+i,4*i+1+j] = t[i]**(3-j) #pi(t)

        for j in range(5):
            tMatrix[2*len(t),j] = (4-j)*t[0]**(3-j) #v0(t)
            tMatrix[3*len(t)-2,-2] = -1 #-vn(0)
            tMatrix[3*len(t)-1,j] = (4-j)*(3-j)*t[0]**(3-j) #a0(t)
            tMatrix[4*len(t)-3,-3] = -2 #-an(0)
        for i in range(1,len(t)-1):
            tMatrix[2*len(t)+i-1,4*i+3] = -1 #vi(0)
            tMatrix[3*len(t)+i-2,4*i+2] = -2 #-ai0)
            for j in range(4):
                tMatrix[2*len(t)+i,i*4+j+1] = (3-j)*t[i]**(2-j) #vi(t)
                tMatrix[3*len(t)+i-1,i*4+j+1] = (3-j)*(2-j)*t[i]**(1-j) #vi(t)

        tMatrix[-4,3] = 1 #v0
        tMatrix[-3,2] = 2 #a0
        for j in range(5):
            tMatrix[-2,j-5] = (4-j)*t[-1]**(3-j) #vt
            tMatrix[-1,j-5] = (4-j)*(3-j)*t[-1]**(2-j) #at

        kMatrix = np.matmul(np.linalg.inv(tMatrix),xMatrix)
        return kMatrix


# ?????????
def main():
    print("start!")

    rospy.init_node('mavgnc', anonymous=True)
    cnt = Controller()
    rate = rospy.Rate(100)

    # ????????????????????????
    rospy.Subscriber('mavros/state', State, cnt.stateCb)
    # ??????optitrack??????????????????????????????
    rospy.Subscriber("/vrpn_client_node/danzhe/pose", PoseStamped, cnt.posCb)
    # ????????????????????????????????????
    rospy.Subscriber("/mavros/local_position/pose", PoseStamped,cnt.refCb)
    rospy.Subscriber("/mavros/local_position/velocity", PoseStamped,cnt.vrefCb)

    add_thread = threading.Thread(target = thread_job)
    add_thread.start()
    # print("enter main!!!!!!!!!!!!!!!!!")
    # sp_pub = rospy.Publisher("mavros/setpoint_position/local", PoseStamped, queue_size = 1)
    cnt.plan([0,0],[0,0.2],[1,1])
    # print("enter loop???????????????")
    flag = 1
    # ROS main loop
    while not rospy.is_shutdown():      
        cnt.current_time.data = time()-cnt.time_init
        if cnt.status == 'Hover':
            print("enter hover!!!!!!!!!!")
            cnt.is_at_setpoint()
            cnt.position_control_fb()
            cnt.velocity_control_fb()
            cnt.start_t = time()
            cnt.send_att()
        else:
            print("enter planning!!!!!!!!!!!!!!!")
            '''
            if flag == 1:
                cnt.pos_err_sum = np.zeros(3)
                cnt.vel_err_sum = np.zeros(3)
                flag = 0
            '''
            cnt.current_t = time()-cnt.start_t
            cnt.current_time.data = cnt.current_t
            cnt.planner()
            cnt.position_control()
            cnt.velocity_control()
        # cnt.target_sp.header.stamp = rospy.Time.now()
            cnt.send_att()
        # sp_pub.publish(cnt.target_sp)
        # cnt.plot_states()
        # plt.show()
        rate.sleep()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
