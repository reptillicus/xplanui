import logging
import xplan_api.request_utils as request
import xplan_api.sbol.sbh as sbh
import xplan_api.doe_utils as doe_utils
import xplan_api.xplan as xplan
from xplan_api.entities import Factor
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MediaChoiceNotAvailableError(Exception): pass

def get_spectro_data_points(resources, media_replicates=1):

    flourescein_factors = [
        {'name': Factor.IGEM, 'values': [x for x in resources['blank_colonies_fluorescein']]},
        {'name': Factor.REPLICATE, 'values': range(0, 4)}
    ]

    ludox_factors = [
        {'name': Factor.IGEM, 'values': [x for x in resources['blank_colonies_ludox']]},
        {'name': Factor.REPLICATE, 'values': range(0, 4)}
    ]

    blank_factors = [
        {'name': Factor.IGEM, 'values': [x for x in resources['blank_colonies_water']]},
        {'name': Factor.REPLICATE, 'values': range(0, 4)}
    ]

    media_factors = [
        {'name': Factor.MEDIA, 'values': resources['media']},
        {'name': Factor.REPLICATE, 'values': range(0, media_replicates)},
        {'name' : Factor.BLANK, 'values' : ["True"]}
    ]

    data_points = doe_utils.get_factorial_design(media_factors)  + \
        doe_utils.get_factorial_design(flourescein_factors) + \
        doe_utils.get_factorial_design(ludox_factors) + \
        doe_utils.get_factorial_design(blank_factors)
    ## print(media_factors)
    ## print(flourescein_factors)
    ## print(ludox_factors)
    ## print(blank_factors)
    return data_points

def get_bead_data_points(resources, bead_factor_replicates, use_only_rainbow=False):
    if use_only_rainbow:
        bead_colony_values = [r for r in resources['bead_colonies'] if 'beads_spherotech_rainbow' in r["name"]]
    else:
        bead_colony_values = resources['bead_colonies']

    bead_factors = [
        {'name': Factor.BEAD_COLONY, 'values': bead_colony_values},
        {'name': Factor.REPLICATE, 'values': range(0, bead_factor_replicates)}
    ]

    data_points = doe_utils.get_factorial_design(bead_factors)

    return data_points

def inducer_uri(inducer):
    return inducer['inducer']['value']


def inducer_pos_vals(inducer):
    return inducer['inducer']['possible_values']


def set_inducer_pos_vals(inducer, vals):
    inducer['inducer']['possible_values'] = vals


def add_inducer_values(data):
    """
    Add the possible values to the query results
    """
    uri = inducer_uri(data)
    vals = []
    if 'Larabinose' in uri:
        vals = ['0', '5']
    elif 'IPTG' in uri:
        vals = ['0', '1']
    elif 'aTc' in uri:
        vals = ['0', '0.002']

    set_inducer_pos_vals(data, vals)

def gate_info(colony_data):
    """
    Get the base id for a colony URI.
    SBH does not specify the gate type of each colony.
    Need to specify gate here to preserve existing functionality.
    """
    mapping = {'UWBF_16967': {'base_id': 'UWBF_XOR', 'input': [1, 1]},
               'UWBF_16968': {'base_id': 'UWBF_XOR', 'input': [1, 0]},
               'UWBF_16969': {'base_id': 'UWBF_XOR', 'input': [0, 1]},
               'UWBF_16970': {'base_id': 'UWBF_XOR', 'input': [0, 0]},
               'UWBF_5783': {'base_id': 'UWBF_OR', 'input': [1, 0]},
               'UWBF_5992': {'base_id': 'UWBF_OR', 'input': [1, 1]},
               'UWBF_5993': {'base_id': 'UWBF_OR', 'input': [0, 1]},
               'UWBF_6388': {'base_id': 'UWBF_NOR', 'input': [0, 1]},
               'UWBF_6389': {'base_id': 'UWBF_NOR', 'input': [1, 0]},
               'UWBF_6390': {'base_id': 'UWBF_NOR', 'input': [0, 0]},
               'UWBF_6391': {'base_id': 'UWBF_NOR', 'input': [1, 1]},
               'UWBF_7299': {'base_id': 'UWBF_XNOR', 'input': [1, 1]},
               'UWBF_7300': {'base_id': 'UWBF_XNOR', 'input': [0, 0]},
               'UWBF_7373': {'base_id': 'UWBF_AND', 'input': [1, 0]},
               'UWBF_7374': {'base_id': 'UWBF_AND', 'input': [1, 1]},
               'UWBF_7375': {'base_id': 'UWBF_AND', 'input': [0, 1]},
               'UWBF_7376': {'base_id': 'UWBF_AND', 'input': [0, 0]},
               'UWBF_7377': {'base_id': 'UWBF_XNOR', 'input': [1, 0]},
               'UWBF_8225': {'base_id': 'UWBF_OR', 'input': [0, 0]},
               'UWBF_8231': {'base_id': 'UWBF_XNOR', 'input': [0, 1]},
               'UWBF_8542': {'base_id': 'UWBF_NAND', 'input': [1, 1]},
               'UWBF_8543': {'base_id': 'UWBF_NAND', 'input': [1, 0]},
               'UWBF_8544': {'base_id': 'UWBF_NAND', 'input': [0, 0]},
               'UWBF_8545': {'base_id': 'UWBF_NAND', 'input': [0, 1]},
               'UWBIOFAB_22544': {'base_id': 'UWBF_WT', 'input': None}}

    for chunk in mapping.keys():
        if chunk in colony_data['gate']:
            return mapping[chunk]

def func(gate, my_input):
    gates = {
        "UWBF_XOR" : lambda i1, i2: not (i1 == i2),
        "UWBF_AND" : lambda i1, i2: i1 and i2,
        "UWBF_NAND" : lambda i1, i2: not ( i1 and i2),
        "UWBF_NOR" : lambda i1, i2: not ( i1 or i2),
        "UWBF_OR" : lambda i1, i2:  i1 or i2,
        "UWBF_XNOR" : lambda i1, i2: i1 == i2,
        }
    lam = gates[gate]
    return lam(bool(my_input[0]), bool(my_input[1]))

def get_strain(resources, gate, inputs):
    for x in resources["colonies"]:
        print(x["gate"])
    gate_strain=[x["gate"] for x in resources["colonies"]
                 if (gate_info(x)["base_id"] == gate and
                     gate_info(x)["input"] == inputs)]
    if len(gate_strain) > 0:
        return gate_strain[0]
    else:
        return None

def yeast_gates_doe(lab, experiment_set, experiment_id,
                    gate, configuration_files, media_choice=None,
                    bead_factor_replicates=1, media_replicates=1,
                    use_only_rainbow=False):

    ## Plan Metadata ##
    metadata = request.get_plan_metadata(experiment_set,
                                         lab,
                                         configuration_files)
    # Overriding experiment_id until SBH is online
    metadata['experiment_id'] = experiment_id

    ## Experimental Resources ##

    resources = sbh.get_experiment_resources(metadata['experiment_set'])
    # removing irrelevant strains
    resources['colonies'] = [x for x in resources['colonies'] if gate_info(x)['base_id'] == gate]
    print(resources["colonies"])
    # assert(len(resources['colonies']) == 5)

    ## DOE Setup ##

    replicates = range(0, 6)
    optical_densities = [0.0003, 0.00015, 0.000075]
    colonies = resources['colonies']
    time_points = [1]


    ## Exerimental Factors ##


    #bb_colonies = resources['dyes'] + resources['bead_colonies']

    if media_choice is None:
        resources['media']=[resources['media'][0]] #Just use one media
    else:
        try:
            if media_choice < 0:
                # Don't allow reverse indexing
                raise IndexError()
            resources['media'] = [resources['media'][media_choice]]
        except IndexError:
            err_msg = 'Provided media choice, {}, is not between 0 and {}'.format(
                media_choice, len(resources['media'])
            )
            if len(resources['media']) == 0:
                err_msg = 'No media choices are available'

            raise MediaChoiceNotAvailableError(err_msg)

    factors = [
        {'name': Factor.STRAIN, 'values': colonies},
        {'name': Factor.REPLICATE, 'values': replicates},
        {'name': Factor.MEDIA, 'values': resources['media']},
        {'name': Factor.OD, 'values' : optical_densities},
        {'name': Factor.TIMEPOINT, 'values' : time_points },
        {'name': Factor.TARGET, 'values' : [True]}

    ]


    promoters={
        "UWBF_XOR" : ["pADH1:iRGR-r3","pGRR:RGR-r6"],
        "UWBF_AND" : ["pADH1:RGR-r2","pGRR-r5:RGR-r1"],
        "UWBF_NAND" : ["pADH1:RGR-r2", "pGRR-nullnull:RGR-r10"],
        "UWBF_NOR" : ["pADH1:RGR-r7","pADH1:RGR-r5"],
        "UWBF_OR" : ["pADH1:iRGR-r3","pGRR:RGR-r6"],
        "UWBF_XNOR" : ["pADH1:iRGR-r3","pGRR:RGR-r6"]
        }

    inputs = [
        [0, 0],
        [0, 1],
        [1, 0],
        [1, 1]
    ]
    mappings =  {
                    "design_name": {
                        gate + "_00": [0, 0],
                        gate + "_01": [0, 1],
                        gate + "_10": [1, 0],
                        gate + "_11": [1, 1]
                    }
                }

    intent = {
        "outcome-variables" : [
            {
                "name": "GFP",
                "statistical-datatype": "counts"
            }
        ],
        "experimental-variables" : [
            {
                "name": "design_name",
                "statistical-datatype": "nominal"
            }
        ],
        "diagnostic-variables" : [
            {
                "name": "media_name",
                "statistical-datatype": "nominal"
            },
            {
                "name": "target_od",
                "statistical-datatype": "nominal"
            }
        ],
        "controls": [
            {
                "design_name":"UWBIOFAB_Scerevisiae_MATa/alpha"
            }
        ],
        "truth-table" : {
            "input-variable-order": [
                "design_name"
            ],
            "mappings" : mappings,
            "output-variable": "GFP",
            "input" : inputs,
            "output" : [ int(func(gate, i)) for i in inputs ]
        },
        "search": {
            "sql": [
                    "SELECT                                                   ",
                    "   design_name                                           ",
                    "   AVG(misbehaving_row) AS probability_surprising        ",
                    "   FROM circuit_analysis_results                         ",
                    "      GROUP BY                                           ",
                    "           design_name                                   ",
                    "           ORDER BY probability_surprising DESC          "
                ]
        }
    }

    stain_factors = [
        {'name': Factor.STAIN, 'values': resources['stains']}
    ]

    data_points = doe_utils.get_factorial_design(factors) + \
        get_spectro_data_points(resources, media_replicates) + \
        get_bead_data_points(resources, bead_factor_replicates, use_only_rainbow) + \
        doe_utils.get_factorial_design(stain_factors)

    p = request.get_planner_problem(metadata, resources, data_points)
    # print(p)
    # xp = xplan.XPlan()
    # xp.run_xplan(str(p), json_output_path='/tmp/plan',
    #           pdf_output_path='/tmp/plan.pdf',
    #           sample_attribute_path='/tmp/sample_attributes.json')
    # xp.add_intent('/tmp/plan', intent)
    return p
