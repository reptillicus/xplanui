import logging
import json
import io
import datetime
import urllib
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from xplan_api import request_utils
from xplan_api import sbol
import xplan_api.xplan as xplan
from portal import utils
from agavepy.agave import Agave

def get_experiment_sets(request):
    exp_sets = request_utils.known_methods
    print(request.user)
    return JsonResponse(exp_sets, safe=False)


def get_resources(request):
    exp_set = request.GET.get("experiment_set", None)
    gate = request.GET.get("gate", None)
    resources = sbol.sbh.get_experiment_resources(exp_set)
    resources['colonies'] = [x for x in resources['colonies'] if utils.gate_info(x)['base_id'] == gate]
    return JsonResponse(resources["colonies"], safe=False)


def get_media(request):
    exp_set = request.GET.get("experiment_set", None)
    media = sbol.sbh.get_experiment_set_media(exp_set)
    return JsonResponse(media, safe=False)

@require_POST
def get_metadata(request):
    data = json.loads(request.body.decode("utf-8"))
    logging.info(data)
    experiment_set = data["experiment_set"]

@require_POST
def create_plan(request):
    data = json.loads(request.body.decode("utf-8"))
    logging.info(data)
    experiment_set = data["experiment_set"]
    experiment_id = data["experiment_id"]
    lab = data["lab"]
    gate = data["gate"]
    media = data["media"]
    replicates = data["replicates"]

    conf_files = {
        "transcriptic": [
            {
                "measurement" : "flow_cytometry",
                "config" : "accurri/5539/11272017/cytometer_configuration.json"
            },
            {
                "measurement" : "spectrophotometry",
                "config" : "synergy_ht/216503/03132018/platereader_configuration.json"
            }
        ],
        "biofab": [
            {"measurement": "flow_cytometry",
             "config": "accuri/5539/11272017/cytometer_configuration.json"},
            {"measurement": "spectrophotometry",
             "config": "synergy_ht/216503/03132018/platereader_configuration.json"}]
    }
    #logger.info("****"*1000)
    configuration_files = conf_files[lab]
    plan = utils.yeast_gates_doe(lab,
        experiment_set,
        experiment_id,
        gate,
        configuration_files,
        media_choice=media,
        bead_factor_replicates=replicates
    )

    #save the file to users home dir and fire the Xplan job using that plan file
    file_obj = io.StringIO(str(plan))
    filename = "xplan-{}".format(datetime.datetime.now().isoformat())
    file_obj.name = filename
    ac = request.user.agave_client
    ac.files.importData(systemId='data-tacc-work-{}'.format(request.user.username),
                                     filePath='/maverick',
                                     fileName=filename,
                                     fileToUpload=file_obj)
    agave_uri = "agave://data-tacc-work-{}/maverick/{}".format(request.user.username,filename)
    job = {
        "appId": "xplan-0.1.0u1",
        "name": "xplan {}".format(datetime.datetime.now().isoformat()),
        "inputs": {
            "problem": agave_uri
        },
        "parameter": {},
        "archive": True
    }
    print(job)

    resp = ac.jobs.submit(body=job)
    return JsonResponse({
        "file": agave_uri,
        "job": resp
    })
