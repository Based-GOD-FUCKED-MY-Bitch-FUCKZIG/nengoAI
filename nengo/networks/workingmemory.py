import numpy as np

import nengo
from nengo.networks import EnsembleArray


def InputGatedMemory(n_neurons, dimensions, fdbk_scale=1.0, gate_gain=10,
                     difference_gain=1.0, reset_gain=3,
                     mem_config=None, net=None):
    """Stores a given vector in memory, with input controlled by a gate."""
    if net is None:
        net = nengo.Network(label="Input Gated Memory")

    if mem_config is None:
        mem_config = nengo.Config(nengo.Connection)
        mem_config[nengo.Connection].synapse = nengo.Lowpass(0.1)

    n_total_neurons = n_neurons * dimensions

    with net:
        # integrator to store value
        with mem_config:
            net.mem = EnsembleArray(n_neurons, dimensions,
                                    neuron_nodes=False, label="mem")
            nengo.Connection(net.mem.output, net.mem.input,
                             transform=fdbk_scale)

        # calculate difference between stored value and input
        net.diff = EnsembleArray(n_neurons, dimensions,
                                 neuron_nodes=False, label="diff")
        nengo.Connection(net.mem.output, net.diff.input, transform=-1)

        # feed difference into integrator
        with mem_config:
            nengo.Connection(net.diff.output, net.mem.input,
                             transform=difference_gain)

        # gate difference (if gate==0, update stored value,
        # otherwise retain stored value)
        net.gate = nengo.Ensemble(50, 1, encoders=nengo.dists.Choice([[1]]),
                                    intercepts=nengo.dists.Uniform(0.4, 0.9))
        #net.gate = nengo.Node(size_in=1)
        for ens in net.diff.all_ensembles:
            nengo.Connection(net.gate, ens.neurons,
                             transform=np.ones((ens.n_neurons, 1)) * -gate_gain,
                             synapse=0.005)
        #nengo.Connection(net.gate, net.diff.neuron_input,
        #                 transform=np.ones((n_total_neurons, 1)) * -gate_gain,
        #                 synapse=None)

        # reset input (if reset=1, remove all values, and set to 0)
        net.reset = nengo.Ensemble(50, 1, encoders=nengo.dists.Choice([[1]]),
                                    intercepts=nengo.dists.Uniform(0.4, 0.9))
        #nengo.Connection(net.reset, net.mem.neuron_input,
        #                 transform=np.ones((n_total_neurons, 1)) * -reset_gain,
        #                 synapse=None)
        for ens in net.mem.all_ensembles:
            nengo.Connection(net.reset, ens.neurons,
                             transform=np.ones((ens.n_neurons, 1)) * -reset_gain,
                             synapse=0.005)

    net.input = net.diff.input
    net.output = net.mem.output

    return net
