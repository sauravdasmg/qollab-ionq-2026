"""Legal strategies. Physical wires 0,1 are references; 2,3 are provers."""
import math
import numpy as np

DEVELOPMENT_SEEDS = tuple(range(2026102900, 2026102908))
LAMBDA_MENU = (.005, .01, .02, .03, .04, .06)
OWNERSHIP = {"reference": [0, 1], "prover": [2, 3]}

def basis_measure_prepare_choi(input_angle=0., output_angles=(0.,0.)):
    """Restricted real basis measurement followed by basis-state preparation.

    Return exact CPTP Choi, output tensor input. output_angles=(0,0) is
    the constant-output |0> control represented by the factory's ideal
    outcome-equivalent circuit. Generic channels here are analysis controls;
    realizing them on hardware requires environments/ancillas.
    """
    c,s=math.cos(input_angle),math.sin(input_angle)
    basis=np.array([[c,-s],[s,c]])
    j=np.zeros((4,4),complex)
    for i,angle in enumerate(output_angles):
        prepared=np.array([math.cos(angle),math.sin(angle)])
        k=np.outer(prepared,basis[:,i].conj())
        v=k.reshape(4)
        j+=np.outer(v,v.conj())
    return j

def frozen_recipe(case=0):
    if isinstance(case, bool) or not isinstance(case, int) or not 0 <= case <= 8:
        raise ValueError("case must be anchor 0 or frozen development case 1..8")
    seed = None if case == 0 else DEVELOPMENT_SEEDS[case-1]
    rng = np.random.default_rng(seed) if seed is not None else None
    return {"identity": "anchor-v2" if case == 0 else f"development-v2-{case}",
            "seed": seed, "alpha": math.pi/4 + (rng.uniform(-.04,.04) if rng else 0),
            "theta": math.pi/8 + (rng.uniform(-.04,.04) if rng else 0),
            "joint_phase": math.pi, "local_rotation": 0.,
            "lambda_star": .02, "lambda_selection": "predeclared; no development selection evidence",
            "menu_lambda": list(LAMBDA_MENU), "objective_evaluations_per_class_per_lambda": 256,
            "optimized_status": "frozen candidate; optimization not yet evidenced"}

def strategy_angles(qc, recipe, candidate):
    if candidate in ("published_hedge", "optimized_joint"):
        # Flip |00> of the prover pair, leaving |01>, |10>, |11> unchanged.
        qc.x(2); qc.x(3)
        qc.cp(math.pi if candidate == "published_hedge" else float(recipe["joint_phase"]), 2, 3)
        qc.x(2); qc.x(3)
        if candidate == "optimized_joint":
            for p in (2,3):
                qc.rz(float(recipe.get("local_phase",0.)),p)
                qc.ry(float(recipe.get("local_rotation",0.)),p)
    elif candidate == "product_control":
        # Ideal outcome-equivalent circuit for fixed-output basis control;
        # see factory assumptions. Never interpret it as a noisy CPTP control.
        pass
    elif candidate != "attained_product":
        raise ValueError("unknown candidate")

def audit_prover_ownership(circuit, start_index, allowed, end_index=None):
    """Audit all nested definitions with local-to-physical wire mapping."""
    def visit(op, wires, ancestry):
        if any(w not in allowed for w in wires):
            raise ValueError(f"illegal strategy wire access: {op.name} {wires}")
        if op.name in {"measure","reset","if_else","switch_case","for_loop","while_loop"} or getattr(op,"condition",None):
            raise ValueError("nonunitary/dynamic strategy instruction")
        definition = op.definition
        if definition is not None:
            if id(op) in ancestry:
                raise ValueError("recursive strategy definition")
            for item in definition.data:
                visit(item.operation, [wires[definition.find_bit(q).index] for q in item.qubits], ancestry | {id(op)})
    for item in circuit.data[start_index:end_index]:
        visit(item.operation,[circuit.find_bit(q).index for q in item.qubits],set())
