from flask import Flask, jsonify, request
from flask_cors import CORS
from agf_init import Robot,mb_client,work_status,task_chain
from agf_work_status import AGF_Status

app = Flask(__name__)
CORS(app=app)

#API Task Chain
def check_point(point:str) -> bool:
    try:
        if point[0:2] == 'LM':
            num = int(point[2:])
            return True
        return False
    except Exception as e:
        return False
def check_wait_time(time:int) -> bool:
    try:
        num = int(time)
        return True
    except Exception as e:
        return False

@app.route('/task_chain',methods=['POST'])
def post_task_chain():
    try:
        content = request.json
        if (work_status.agf_status == AGF_Status.AGF_Status_Busy) or (len(work_status.agf_error) > 0) or (work_status.agf_work_mode != content['work_mode']): 
            return jsonify({"result":False,"desc":""}),200
        check_task = True
        keys = content.keys()
        if 'loop' in keys and 'task_list' in keys and 'agf_id' in keys:
            loop = content['loop']
            task_list = content['task_list']
            if len(task_list) > 0:
                for task in task_list:
                    keys = task.keys()
                    if 'task_name' in keys:
                        if task['task_name'] == 'pick':
                            if ('pick_point' in keys) and ('detect_point' in keys):
                                if not check_point(point=task['pick_point']) or not check_point(point=task['detect_point']):
                                    check_task = False
                        elif task['task_name'] == 'put':
                            if ('put_point' in keys):
                                if not check_point(point=task['put_point']):
                                    check_task = False
                        elif task['task_name'] == 'navigation':
                            if 'target_point' in keys:
                                if not check_point(point=task['target_point']):
                                    check_task = False
                        elif task['task_name'] == 'wait':
                            if 'wait_time' in keys:
                                if not check_wait_time(task['wait_time']):
                                    check_task = False
                        else:
                            check_task = False
        if check_task:
            work_status.agf_status = AGF_Status.AGF_Status_Busy
            task_chain.task_list = task_list
            task_chain.loop = loop
            return jsonify({"result":True,"desc":""}),201
        return jsonify({"result":False,"desc":""}),200
    except Exception as e:
        return jsonify({"result":False,"desc":str(e)}),500
# API AMR
@app.route('/work_mode',methods = ['POST','PUT'])
def post_mode_agf():
    try:
        content = request.json
        keys = content.keys()
        if 'work_mode' in keys:
            if content['work_mode'] == 'Manual' or content['work_mode'] == 'Auto':
                # AGF_Work_Status['work_mode'] = content['work_mode']
                work_status.agf_work_mode = content['work_mode']
                return jsonify({'result':True,'desc':''}),201
        return jsonify({'result':False,'desc':''}),204
    except Exception as e:
        return jsonify({"result":False,"desc":str(e)}),500

@app.route('/status',methods = ['GET'])
def get_status_amr():
    try:
        Robot.data_Status['work_status'] = work_status.get_agf_work_status()
        return jsonify(Robot.data_Status),200
    except Exception as e:
        return jsonify({"result":False,"desc":str(e)}),500
    
@app.route('/cancel',methods=['PUT','POST'])
def cancel_mission_agf():
    if task_chain.task_current != {}:
        task_chain.task_signal_cancel = True
        return jsonify({"result":True,"desc":""}),201
    else:
        return jsonify({"result":False,"desc":""}),400
        


# Route mặc định
@app.route('/pause',methods=['PUT','POST'])
def pause_nav():
    if Robot.pause_navigation():
        return jsonify({"result":True,"desc":""}),201
    else:
        return jsonify({"result":True,"desc":""}),400

@app.route('/resume',methods=['PUT','POST'])
def resume_nav():
    if Robot.resume_navigation():
        return jsonify({"result":True,"desc":""}),201
    else:
        return jsonify({"result":True,"desc":""}),400

@app.route('/relocation', methods=["POST"])
def re_location():
    content = request.json
    if content:
        print("content", content)
        Robot.re_location(content)
    return content, 200

@app.route('/navigation', methods=["POST"])
def navigation():
    content = request.json
    if content:
        print("content", content)
        Robot.navigation(content)
    return content, 200

@app.route('/confirm', methods=["POST"])
def confirm():
    content = request.json
    if content:
        print("content", content)
        Robot.confim_location()
    return content, 200

@app.route('/control_amr', methods=["POST"])
def monitor():
    content = request.json
    if content:
        Robot.monitor(content)
    return content, 200

def lift_manual_control(control:dict):
    '''
    arg1 is dict:
    {
        "type":"slider" or "lift",
        "value":"up" or "down" or "in" or "out"
    }
    '''
    if control["type"] == "slider":
        if control["value"] == "in":
            mb_client.hold_regs[10] = 0
            mb_client.hold_regs[11] = 1
            mb_client.hold_regs[0] = 0
        elif control["value"] == "out":
            mb_client.hold_regs[10] = 0
            mb_client.hold_regs[11] = 2
            mb_client.hold_regs[0] = 0
        elif control["value"] == "stop":
            mb_client.hold_regs[10] = 0
            mb_client.hold_regs[11] = 0
            mb_client.hold_regs[0] = 0
    elif control["type"] == "lift":
        mb_client.hold_regs[10] = 0
        mb_client.hold_regs[0] = 0
        mb_client.hold_regs[12] = control["value"]

@app.route('/lift',methods=['PUT','POST'])
def lift_control():
    try:
        content = request.json
        keys = content.keys()
        if 'lift' in keys and work_status.agf_status == AGF_Status.AGF_Status_Idle and len(work_status.agf_error) == 0:
            lift_manual_control({"type":"lift","value":content['lift']})
            return jsonify({"result":True,"desc":""}),201
        return jsonify({"result":False,"desc":""}),400
    except Exception as e:
        return jsonify({"result":False,"desc":str(e)}),500

@app.route('/slider',methods=['PUT','POST'])
def slider_control():
    try:
        content = request.json
        keys = content.keys()
        if 'slider' in keys and work_status.agf_status == AGF_Status.AGF_Status_Idle and len(work_status.agf_error) == 0:
            if content['slider'] == 'in':
                lift_manual_control({"type":"slider","value":"in"})
                return jsonify({"result":True,"desc":""}),201
            elif content['slider'] == 'out':
                lift_manual_control({"type":"slider","value":"out"})
                return jsonify({"result":True,"desc":""}),201
            elif content['slider'] == 'stop':
                lift_manual_control({"type":"slider","value":"stop"})
                return jsonify({"result":True,"desc":""}),201
        return jsonify({"result":False,"desc":""}),400
    except Exception as e:
        return jsonify({"result":False,"desc":str(e)}),500
