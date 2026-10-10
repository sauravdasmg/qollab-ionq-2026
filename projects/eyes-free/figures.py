"""Accessible chart uses the same measured fit as text and audio."""
import numpy as np
import matplotlib.pyplot as plt


def chart(estimates, label):
    fig, ax = plt.subplots()
    for index, e in enumerate(estimates):
        x = np.array(e["phases_rad"])
        ax.plot(x, e["parity"], marker=("o", "s", "^")[index % 3],
                label="series %d: f=%.4f, C=%.4f (%s)" % (index+1, e["frequency"], e["contrast"], e["flag"]))
    ax.set(xlabel="Phase (radians)", ylabel="Measured parity (unitless)", title=label, ylim=(-1.1, 1.1))
    ax.legend(fontsize="small")
    fig.tight_layout()
    return fig
