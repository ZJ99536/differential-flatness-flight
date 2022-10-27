from cProfile import label
import numpy as np
import matplotlib.pyplot as plt
file_name = "text01.txt"
save_name = "text.png"
read_path = "C:/Users/Juliazhou/Desktop/differential-flatness-flight/test01.txt"

data = np.loadtxt(read_path, delimiter=',', dtype='float32', skiprows=1)
print(data)
fig, ax = plt.subplots(4, 3, figsize=(14, 10))

ax[0][0].plot(data[:, 0], 'r-')  # 7  8  9     13 14 15   19 20 21
ax[0][1].plot(data[:, 1], 'r-')  # 7  8  9     13 14 15   19 20 21
ax[0][2].plot(data[:, 2], 'r-')  # 7  8  9     13 14 15   19 20 21
ax[0][0].plot(data[:, 3], 'b-')  # 7  8  9     13 14 15   19 20 21
ax[0][1].plot(data[:, 4], 'b-')  # 7  8  9     13 14 15   19 20 21
ax[0][2].plot(data[:, 5], 'b-')  # 7  8  9     13 14 15   19 20 21
ax[1][0].plot(data[:, 6], 'r-')  # 7  8  9     13 14 15   19 20 21
ax[1][1].plot(data[:, 7], 'r-')  # 7  8  9     13 14 15   19 20 21
ax[1][2].plot(data[:, 8], 'r-')  # 7  8  9     13 14 15   19 20 21
# ax[1][0].plot(data[:, 9], 'b-')  # 7  8  9     13 14 15   19 20 21
# ax[1][1].plot(data[:, 10], 'b-')  # 7  8  9     13 14 15   19 20 21
# ax[1][2].plot(data[:, 11], 'b-')  # 7  8  9     13 14 15   19 20 21
ax[2][0].plot(data[:, 12], 'r-')  # 7  8  9     13 14 15   19 20 21
ax[2][1].plot(data[:, 13], 'r-')  # 7  8  9     13 14 15   19 20 21
ax[2][2].plot(data[:, 14], 'r-')  # 7  8  9     13 14 15   19 20 21
ax[3][0].plot(data[:, 18], 'r-')  # 7  8  9     13 14 15   19 20 21
ax[3][1].plot(data[:, 19], 'r-')  # 7  8  9     13 14 15   19 20 21
ax[3][2].plot(data[:, 20], 'r-')  # 7  8  9     13 14 15   19 20 21
# ax[i][j].plot(data[:,0], data[:,i*6+j+4], 'b-') # 10 11 12    16 17 18   22 23 24


ax[0, 0].set_title("position x")
ax[0, 1].set_title("position y")
ax[0, 2].set_title("position z")
ax[1, 0].set_title("velocity x")
ax[1, 1].set_title("velocity y")
ax[1, 2].set_title("velocity z")
ax[2, 0].set_title("attitude x")
ax[2, 1].set_title("attitude y")
ax[2, 2].set_title("attitude z")
ax[3, 0].set_title("body_rate x")
ax[3, 1].set_title("body_rate y")
ax[3, 2].set_title("body_rate z")

save_path = "C:/Users/Juliazhou/Desktop/differential-flatness-flight/text.png"
plt.savefig(save_path, dpi=300)
plt.show()
'''

# for i in range(3):
#     ax[0][i].plot(data[:,0], data[:,i+1], 'r*', label="local")

# ax[0][0].plot(data[:,0], 1*np.ones((data.shape[0],1)), 'b-', label = "target")
# ax[0][1].plot(data[:,0], 1*np.ones((data.shape[0],1)), 'b-', label = "target")
# ax[0][2].plot(data[:,0], 1.5*np.ones((data.shape[0],1)), 'b-', label = "target")

for i in range(2):
    for j in range(3):
        ax[i][j].plot(data[:,0], data[:,i*6+j+1], 'r-')  # 7  8  9     13 14 15   19 20 21
        ax[i][j].plot(data[:,0], data[:,i*6+j+4], 'b-') # 10 11 12    16 17 18   22 23 24

for j in range(3):
    ax[2][j].plot(data[:,0], data[:,12+j+1], 'r-', label = "current")  # 7  8  9     13 14 15   19 20 21
    ax[2][j].plot(data[:,0], data[:,12+j+4], 'b-', label = "feedfoward") # 10 11 12    16 17 18   22 23 24
    ax[2][j].plot(data[:,0], data[:,12+j+7], 'y-', label = "feedback")
    # ax[3][j].plot(data[:,0], data[:,21+j+1], 'r-')
    # ax[3][j].plot(data[:,0], data[:,21+j+4], 'b-')
    # ax[3][j].plot(data[:,0], data[:,21+j+7], 'y-')


for j in range(3):
    # ax[4][j].plot(data[:,0], data[:,33], 'r-')
    # ax[4][j].plot(data[:,0], data[:,34], 'b-')
    ax[0][j].set_ylabel("x/m")
    ax[0][j].set_xlabel("t/s")
    ax[1][j].set_ylabel("v/m/s")
    ax[1][j].set_xlabel("t/s")
    ax[2][j].set_ylabel("e/deg")
    ax[2][j].set_xlabel("t/s")
    ax[3][j].set_ylabel("r/rad/s")
    ax[3][j].set_xlabel("t/s")
    # ax[4][j].set_ylabel("a/m/s*2")
    # ax[4][j].set_xlabel("t/s")

ax[0, 0].set_title("position x")
ax[0, 1].set_title("position y")
ax[0, 2].set_title("position z")
ax[1, 0].set_title("velocity x")
ax[1, 1].set_title("velocity y")
ax[1, 2].set_title("velocity z")
ax[2, 0].set_title("attitude x")
ax[2, 1].set_title("attitude y")
ax[2, 2].set_title("attitude z")
ax[3, 0].set_title("body_rate x")
ax[3, 1].set_title("body_rate y")
ax[3, 2].set_title("body_rate z")
# ax[0, 0].set_title("pos x")
# ax[0, 1].set_title("pos y")
# ax[0, 2].set_title("pos z")
# ax[1, 0].set_title("vel x")
# ax[1, 1].set_title("vel y")
# ax[1, 2].set_title("vel z")
# ax[2, 0].set_title("euler x")
# ax[2, 1].set_title("euler y")
# ax[2, 2].set_title("euler z")
# ax[3, 0].set_title("body_rate x")
# ax[3, 1].set_title("body_rate y")
# ax[3, 2].set_title("body_rate z")
# ax[4, 0].set_title("acceleration z")
# ax[4, 1].set_title(" ")
# ax[4, 2].set_title(" ")
lines, labels = fig.axes[-1].get_legend_handles_labels()
fig.legend()
fig.tight_layout()
save_path = "C:/Users/mi/Desktop/" + save_name
plt.savefig(save_path, dpi=300)
plt.show()
'''




