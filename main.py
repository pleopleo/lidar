from anyio import sleep
import api.msgpack as MsgpackApi
import api.compact as CompactApi

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


###############################################################################################
#                                     CONFIGURATION                                           #
###############################################################################################

PROTOCOL            = "MSGPACK"
ALL_MEASURMENT_DATA = True
PORT                = 2115
IP                  = "192.168.1.2"
NUMBER_SEGMENT      = 10
PERCENTAGE_ACCEPTED  = 0.5
DISTANCE_LIMITE     = 1000
COUNTER_IT          = 100

##############################################################################################

first_line_x = []
first_line_y = []
second_line_x = [] 
second_line_y = []
start = 1
status_system = 0
counter = 0

def check_array(x, y):
      global status_system  # Declare status_system as a global variable
      global counter

      status = False

      if status_system == 0 and len(x) > 0 and len(y) > 0:
            max_first_line_x = np.max(first_line_x)
            percentage_below_max = np.sum(x < max_first_line_x) / len(x)
            status = percentage_below_max >= PERCENTAGE_ACCEPTED
            if(status):
                  counter = counter+1
            else:
                  counter = 0

            if(status == True and counter == COUNTER_IT):
                  status = True
                  with open('data.txt', 'a') as file:
                        np.savetxt(file, np.column_stack((x, y)), delimiter=',', header='X,Y', comments='')
                  status_system = 1
                  counter = 0
            else: 
                  status = False


            
            return status

      elif status_system == 1 and len(x) > 0 and len(y) > 0:
            max_first_line_x = np.max(second_line_x)
            percentage_below_max = np.sum(x < max_first_line_x) / len(x)
            status = percentage_below_max >= PERCENTAGE_ACCEPTED
           
            if(status):
                  counter = counter+1
            else:
                  counter = 0

            if(status == True and counter == 100):
                  status = True
                  with open('data2.txt', 'a') as file:
                        np.savetxt(file, np.column_stack((x, y)), delimiter=',', header='X,Y', comments='')
                  status_system = 2
                  counter = 0
            else: 
                  status = False
                  
      
      elif status_system == 2:
            print("Lave, redémarrage et calcul nécessaire")

      return status

def send_alarm():
      print("alarme")

if __name__ == "__main__":

      while True :

            distance = []
            rssi = []
            angle = []

            if "MSGPACK" == PROTOCOL:
                  receiver = MsgpackApi.Receiver(port=PORT, host=IP)
            else:
                  receiver = CompactApi.Receiver(port=PORT, host=IP)

            (segments, frameNumbers, segmentCounters) = receiver.receiveSegments(NUMBER_SEGMENT)
            receiver.closeConnection()

            # extract all segments with SegmentCounter = 2
            idx = np.where(np.array(segmentCounters))
            allSeg2 = np.array(segments)[idx]

            # Print all fields with at least one measurement example using MSGPACK protocol
            if "MSGPACK" == PROTOCOL:
                  LAYER_ID = 1    # The scan layer for which the information in this test are requested (e.g. layer with id 1).
                              # It contains all beams for one elevation angle in the observed segment.
                  BEAM     = 0    # The beam index within a layer containing all echos. The beam with index 0 has the azimuth angle ThetaStart.
                  ECHO     = 0    # The echo index for which distance and RSSI values are obtained.

                  for segment in allSeg2:

                        # Find the index of the layer with id LAYER_ID
                        layerIndex = segment["LayerId"].index(LAYER_ID)

                        # All distance data of layer 0
                        if ALL_MEASURMENT_DATA:
                              distance.append(np.array(segment["SegmentData"][layerIndex]["Distance"]))
                              rssi.append(np.array(segment["SegmentData"][layerIndex]["Rssi"]))
                              angle.append(np.array(segment["SegmentData"][layerIndex]["ChannelTheta"]))


            concatenated_distance_data = np.concatenate(distance)
            concatenated_distance_data = concatenated_distance_data[concatenated_distance_data != -1]

            concatenated_rssi_data = np.concatenate(rssi)
            concatenated_rssi_data = concatenated_rssi_data[concatenated_rssi_data != -1]

            concatenated_angle_data = np.concatenate(angle)

            x_values = concatenated_distance_data * np.cos(concatenated_angle_data)
            y_values = concatenated_distance_data * np.sin(concatenated_angle_data)

            # Filter out points where both x and y are zero
            non_zero_indices = np.logical_and(x_values != 0, y_values != 0)
            x_values_filtered = x_values[non_zero_indices]
            y_values_filtered = y_values[non_zero_indices]

            if(start == 1):
                  # Add a line that is a straight line at a closer x-distance and fixed y-distance (1000)
                  first_line_x = np.full(len(x_values_filtered), np.min(x_values_filtered) - 1000)  # Same length as x_values_filtered
                  first_line_y = np.linspace(np.max(y_values_filtered), np.min(y_values_filtered), len(y_values_filtered))

                  second_line_x = np.full(len(x_values_filtered), np.min(x_values_filtered) - 2000)  # Same length as x_values_filtered
                  second_line_y = np.linspace(np.max(y_values_filtered), np.min(y_values_filtered), len(y_values_filtered))

                  start = 0
            
            # Filter out values below DISTANCE in x_values_filtered
            x_values_filtered = x_values_filtered[x_values_filtered > DISTANCE_LIMITE]

            status = check_array(x_values_filtered, y_values_filtered)
            if(status):
                  send_alarm()
                  

            
            # # Plot the 2D scatter plot
            # plt.scatter(x_values_filtered, y_values_filtered)
            # plt.scatter(first_line_x, first_line_y)
            # plt.scatter(second_line_x, second_line_y)

            # # Set labels for the axes
            # plt.xlabel('X')
            # plt.ylabel('Y')

            # # Show the plot
            # plt.show()
