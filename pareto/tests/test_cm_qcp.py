#####################################################################################################
# PARETO was produced under the DOE Produced Water Application for Beneficial Reuse Environmental
# Impact and Treatment Optimization (PARETO), and is copyright (c) 2021-2023 by the software owners:
# The Regents of the University of California, through Lawrence Berkeley National Laboratory, et al.
# All rights reserved.
#
# NOTICE. This Software was developed under funding from the U.S. Department of Energy and the U.S.
# Government consequently retains certain rights. As such, the U.S. Government has been granted for
# itself and others acting on its behalf a paid-up, nonexclusive, irrevocable, worldwide license in
# the Software to reproduce, distribute copies to the public, prepare derivative works, and perform
# publicly and display publicly, and to permit others to do so.
#####################################################################################################


import pyomo.environ as pyo
from importlib import resources
import pytest

from pareto.other_models.CM_module.models.qcp_br import build_qcp_br
from pareto.other_models.CM_module.operational.set_param_list import set_list, parameter_list
from pareto.utilities.cm_utils.opt_utils import (
    max_theoretical_recovery_flow_opt,
    cost_optimal,
    max_recovery_with_infrastructure,
)

from pareto.utilities.cm_utils.data_parser import data_parser
from pareto.utilities.get_data import get_data
from pareto.utilities.cm_utils.run_utils import node_rerun


class TestCMqcpModel:
    def build_cm_qcp_model(self):
        """
        Building critical mineral qcp model to run on the Li small case study
        """

        with resources.path(
            "pareto.case_studies",
            "small_case_study_Li.xlsx",
        ) as fpath:
            [df_sets, df_parameters] = get_data(fpath, set_list, parameter_list)

            data = data_parser(df_sets, df_parameters)

            # building model
            model = build_qcp_br(data)

            return model

    def test_model_data(self):
        """
        The correct objective value must be active
        """
        model = self.build_cm_qcp_model()

        assert model.br_obj.active  # correct objective function is active
        assert not model.obj.active

        assert model.p_Cmin["R01_CW", "Li"].value == 100  # minimum lithium req is 100

    def test_small_case_study(self):
        model = self.build_cm_qcp_model()

        solver = "ipopt"
        opt = pyo.SolverFactory(solver)
        assert opt.available()

        status = opt.solve(model, tee=False)
        pyo.assert_optimal_termination(status)

class TestAddFeatures:
    def obtain_data(self):
        with resources.path(
            "pareto.case_studies",
            "small_case_study_Li.xlsx",
        ) as fpath:
            [df_sets, df_parameters] = get_data(fpath, set_list, parameter_list)

        data = data_parser(df_sets, df_parameters)
        return data
    
    def test_infra_analysis(self):
        data = self.obtain_data()
        print("--- Running cost optimal solution ---")
        model = cost_optimal(data)

        print("--- Running max treatment with infrastructure ---")
        max_inf_model = max_recovery_with_infrastructure(data)

        print("--- Runnning max theoretical treatment revenue ---")
        max_recovery = max_theoretical_recovery_flow_opt(
            model, treatment_unit="R01_IN", desired_li_conc=100
        )

        max_w_infra = pyo.value(max_inf_model.treat_rev)

        assert max_recovery >= max_w_infra
    


if __name__ == "__main__":
    pytest.main()
