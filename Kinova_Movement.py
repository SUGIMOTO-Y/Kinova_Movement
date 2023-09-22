from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient
from kortex_api.autogen.client_stubs.BaseCyclicClientRpc import BaseCyclicClient
from kortex_api.autogen.messages import Base_pb2
import utilities as utilities
import threading

class Movement:
    def __init__(self, parse, Class):
        with utilities.DeviceConnection.createTcpConnection(parse) as router:
            self.TIMEOUT_DURATION = 20
            self.base = BaseClient(router)
            self.base_cyclic = BaseCyclicClient(router)
            self.Class = Class

            self.Move_To_HomePosition()
            self.Move_EachAction()
            self.Move_To_HomePosition()
    
    def check_for_end_or_abort(self, event):
        def check(notification, event = event):
            print("EVENT : " + Base_pb2.ActionEvent.Name(notification.action_event))
            if notification.action_event == Base_pb2.ACTION_END or notification.action_event == Base_pb2.ACTION_ABORT: event.set()
        return check

    def Move_To_HomePosition(self):
        # Make sure the arm is in Single Level Servoing mode
        base_servo_mode = Base_pb2.ServoingModeInformation()
        base_servo_mode.servoing_mode = Base_pb2.SINGLE_LEVEL_SERVOING
        self.base.SetServoingMode(base_servo_mode)
        
        # Move arm to ready position
        print("Moving the arm to a safe position")
        action_type = Base_pb2.RequestedActionType()
        action_type.action_type = Base_pb2.REACH_JOINT_ANGLES
        action_list = self.base.ReadAllActions(action_type)
        action_handle = None
        for action in action_list.action_list:
            if action.name == "Home":
                action_handle = action.handle
        if action_handle == None:
            print("Can't reach safe position. Exiting")

        event = threading.Event()
        notification_handle = self.base.OnNotificationActionTopic(
            self.check_for_end_or_abort(event),
            Base_pb2.NotificationOptions()
        )
        self.base.ExecuteActionFromReference(action_handle)
        finished = event.wait(self.TIMEOUT_DURATION)
        self.base.Unsubscribe(notification_handle)

        if finished: print("Safe position reached")
        else: print("Timeout on action notification wait")

    def Move_EachAction(self):
        print("Starting Cartesian action movement ...")
        action = Base_pb2.Action()
        action.name = "Example Cartesian action movement"
        action.application_data = ""
        feedback = self.base_cyclic.RefreshFeedback()
        for i in range(0, 4):
            if self.Class == i: self.Pose_Action(self.Action_List_(i), action, feedback)

        event = threading.Event()
        notification_handle = self.base.OnNotificationActionTopic(
            self.check_for_end_or_abort(event),
            Base_pb2.NotificationOptions()
        )
        print("Executing action")
        self.base.ExecuteAction(action)
        print("Waiting for movement to finish ...")
        finished = event.wait(self.TIMEOUT_DURATION)
        self.base.Unsubscribe(notification_handle)

        if finished: print("Cartesian movement completed")
        else: print("Timeout on action notification wait")
        
    def Pose_Action(self, List, action, feedback):
        cartesian_pose = action.reach_pose.target_pose
        # (meters)
        cartesian_pose.x = feedback.base.tool_pose_x + List[0]    
        cartesian_pose.y = feedback.base.tool_pose_y + List[1]    
        cartesian_pose.z = feedback.base.tool_pose_z + List[2]    
        # (degrees)
        cartesian_pose.theta_x = feedback.base.tool_pose_theta_x 
        cartesian_pose.theta_y = feedback.base.tool_pose_theta_y 
        cartesian_pose.theta_z = feedback.base.tool_pose_theta_z
    
    def Action_List_(self, i):
        C1 = [-0.15, -0.42, -0.37]
        C2 = [0.06, -0.18 , -0.37]
        C3 = [0.06, 0.08, -0.37]
        C4 = [-0.15, 0.39, -0.37]
        List = [C1, C2, C3, C4]
        return List[i]

if __name__ == '__main__':
    import argparse
    parse_ = argparse.ArgumentParser()
    parse = utilities.parseConnectionArguments(parse_)
    Movement(parse, Class = 0)