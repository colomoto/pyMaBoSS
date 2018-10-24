"""Definitions of the different classes provided to the user."""

from . import logic
from sys import stderr, stdout


class Node(object):
    """
    Represent a node of a boolean network.

     .. py:attribute:: name

       the name of the node

     .. py:attribute:: rt_up

        A string, an expression that will be evaluated by *MaBoSS* to determine
        the probability of the node to switch from down to up

     .. py:attribute:: rt_down

        A string, similar to rt_up but determine the probability to go from up
        to down

     .. py:attribute:: logExp

        A string, the value that will be attributed to the internal node
        variable ``@logic`` in the bnd file

    Node objects have a ``__str__`` method that prints their representation in the
    *MaBoSS* language.
    """

    def __init__(self, name, logExp=None, rt_up=1, rt_down=1,
                 is_internal=False, internal_var={}, is_mutant=False):
        """
        Create a node not yet inserted in a network.

        logic, rt_up and rt_down are optional when creating the node but
        must be set before making a network.
        
        The is_internal attribute determines wether a node will appear in the 
        MaBoSS output or not.
        
        internal_var is a dictionary of the node's internal variables.
        """
        self.name = name
        self.set_logic(logExp)
        self.rt_up = rt_up
        self.rt_down = rt_down
        self.is_internal = is_internal
        self.internal_var = internal_var.copy()
        self.is_mutant=is_mutant

    def set_rate(self, rate_up, rate_down):
        """
        Set the value of rate_up and rate_down.
        
        :param double rate_up: the value of ``rt_up`` in below expression
        :param double rate_down: the value of ``rt_down`` in below expression

        This function will write a simple formula of the form

            ``rate_up = @logic ? rt_up : 0 ;``
            ``rate_down = @logic ? 0 : rt_down ;``
        """
        self.rt_up = "@logic ? " + rate_up + " : 0"
        self.rt_down = "@logic ? 0 : " + rate_down

    def set_logic(self, string):
        """Set logExp to string if string is a valid boolean expression.
        
        :param str string: the boolean expression to be attributed to ``self.logExp``
        """
        if not string:
            self.logExp = None
        if logic._check_logic_syntax(string):
            self.logExp = string
        else:
            print("Warning, syntax error: %s" % string, file=stderr)
            print("logExp set to None", file=stderr)
            self.logExp = None

    def __str__(self):
        return _strNode(self)

    def copy(self):
        return Node(self.name, self.logExp, self.rt_up, self.rt_down,
                    self.is_internal, self.internal_var, self.is_mutant)


class Network(dict):
    """
    Represent a boolean network.

    Initialised with a list of Nodes whose ``logExp`` s must contain only names
    present in the list.
    
    Network objects are in charge of carrying the initial states of each node.
    """

    def __init__(self, nodeList, booleanVariablesList):
        super().__init__({nd.name: nd for nd in nodeList})
        self.names = [nd.name for nd in nodeList]
        self.logicExp = {nd.name: nd.logExp for nd in nodeList}
        self.booleanVariables = booleanVariablesList

        if not logic._check_logic_defined(self.names + self.booleanVariables,
                                          [nd.logExp for nd in nodeList if nd.logExp]):
            raise ValueError("Some logic rule had unkown variables")

        # _attribution gives for each node the list of node with which it is
        # binded.
        self._attribution = {nd.name: nd.name for nd in nodeList}

        # _initState gives for each list of binded node the initial state
        # probabilities.
        self._initState = {l: {0: 0.5, 1: 0.5} for l in self._attribution}

    def copy(self):
        new_ndList = [self[name].copy() for name in self.names]
        new_network = Network(new_ndList, self.booleanVariables)
        new_network._attribution = self._attribution.copy()
        new_network._initState = self._initState.copy()
        return new_network

    def set_istate(self, nodes, probDict):
        """
        Change the inital states probability of one or several nodes.

        :param nodes: the node(s) whose initial states are to be modified
        :type nodes: a :py:class:`Node` or a list or tuple of :py:class:`Node`
        :param dict probDict: the probability distribution of intial states

        If nodes is a Node object or a singleton, probDict must be a probability
        distribution over {0, 1}, it can be expressed by a list [P(0), P(1)] or a
        dictionary: {0: P(0), 1: P(1)}.

        If nodes is a tuple or a list of several Node objects, the Node object 
        will be bound, and probDict must be a probability distribution over a part
        of {0, 1}^n. It must be expressed in the form of a dictionary
        {(b1, ..., bn): P(b1,..,bn),...}. States that do not appear in the 
        dictionary will be considered to be impossible. If a state has a 0 probability of
        being an intial state but might be reached later, it must explicitly appear 
        as a key in probDict.
        
        **Example**
        
        >>> my_network.set_istate('node1', [0.3, 0.7]) # node1 will have a probability of 0.7 of being up
        >>> my_network.set_istate(['node1', 'node2'], {(0, 0): 0.4, (1, 0): 0.6, (0, 1): 0}) # node1 and node2 can never be both up because (1, 1) is not in the dictionary
        """
        if not (isinstance(nodes, list) or isinstance(nodes, tuple)):
            if not len(probDict) in [1, 2]:
                print("Error, must provide a list or dictionary of size 1 or 2",
                      file=stderr)
                return

            if (probDict[0] < 0 or probDict[1] < 0
                  or not probDict[0] + probDict[1] == 1):
                print("Error, bad value for probabilites", file=stderr)
                return
            else:
                if isinstance(self._attribution[nodes], tuple):
                    self._erase_binding(nodes)
                self._initState[nodes] = {0: probDict[0], 1: probDict[1]}

        elif _testStateDict(probDict, len(nodes)):
            for node in nodes:
                if isinstance(self._attribution[node], tuple):
                    print("Warning, node %s was previously bound to other"
                          "nodes" % node, file=stderr)
                    self._erase_binding(node)

            # Now, forall node in nodes, self_attribution[node] is a singleton
            for node in nodes:
                self._initState.pop(node)
                self._attribution[node] = tuple(nodes)

            self._initState[tuple(nodes)] = probDict


    def _erase_binding(self, node):
        self._initState.pop(self._attribution[node])
        for nd in self._attribution[node]:
            self._attribution[nd] = [nd]
            self.set_istate(nd, [0.5, 0.5])


    def __str__(self):
        return _strNetwork(self)


    def print_istate(self, out=stdout):
        print(_str_istateList(self._initState), file=out)

    def set_output(self, output_list):
        """Set all the nodes that are not in the output_list as internal.

        :param output_list: the nodes to remain external
        :type output_list: list of :py:class:`Node`
        """
        for nd in self:
            self[nd].is_internal = nd not in output_list


def _testStateDict(stDict, nbState):
    """Check if stateDict is a good parameter for set_istate."""
    def goodTuple(t):
        return len(t) == nbState and all(x == 0 or x == 1 for x in t)

    if (not all(isinstance(t, tuple) for t in stDict)
       or not all(goodTuple(t) for t in stDict)):
        print("Error, not all keys are good tuples of length %s" % nbState,
              file=stderr)
        return False
    elif not all(x >= 0 for x in stDict.values()):
        print("Error, the given values must be nonegative",
              file=stderr)
        return False
    elif not sum(stDict.values()) == 1:
        print("Warning: the given values should sum up to 1",
              file=stderr)
        return True
    else:
        return True


def _strNode(nd):
    string = ""
    rt_up_str = str(nd.rt_up)
    rt_down_str = str(nd.rt_down)
    internal_var_decl = "\n".join(map(lambda v: v+" = " + nd.internal_var[v],
                                      nd.internal_var.keys()))
    string = "\n".join(["Node " + nd.name + " {",
                        internal_var_decl,
                        ("\tlogic = " + nd.logExp + ";") if nd.logExp else "",
                        ("\trate_up = " + rt_up_str + ";"),
                        ("\trate_down = " + rt_down_str + ";"),
                        "}"])
    return string


def _strNetwork(nt):
    ndList = list(nt.values())
    string = _strNode(ndList[0])
    if len(ndList) > 1:
        string += "\n"
        string += "\n\n".join(_strNode(nd) for nd in ndList[1:])
    return string


def _str_istateList(isl):
    stringList = []
    for binding in isl:
        string = ''
        if isinstance(binding, tuple):
            string += '[' + ", ".join(list(binding)) + '].istate = '
            string += ' , '.join([str(isl[binding][t]) + ' '
                                  + str(list(t)) for t in isl[binding]])
            string += ';'
        else:
            string += '[' + binding + '].istate = '
            string += str(isl[binding][0]) + '[0] , '
            string += str(isl[binding][1]) + '[1];'
        stringList.append(string)
    return '\n'.join(stringList)

