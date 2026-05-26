# MaBoSSEvaluator Help

The tool runs all the simulations that are required to evaluate your queries.

## Syntax

```python
from maboss import MaBoSSEvaluator
MaBoSSEvaluator.querying(queries, cfg_file, bnd_file, [initial_state], [output_setting])

```

* **`query`** : The query to evaluate, a list of strings: `["query1", "query2"]`
* **`cfg_file`** : The path to the configuration file, a string.
* **`bnd_file`** : The path to the binary file, a string.
* **`initial_state`** : The initial state of the simulation, a dictionary like: `[{'node':'name','state':'ON/OFF'}, {'node':'name','state':'ON/OFF'}]`
* **`output_setting`** : The output setting of the simulation, a list of strings: `["output1", "output2"]`. The nodes passed are going to be defined as external.

---

## Help For The Query

The query is a string that contains the following elements:
`[type]([target_type]:name1,name2...) [operator] [value] [logical_equation (optional)] [mutations (opt)] [options]`

### `[type]`

The type of operation to perform. Can be **P** (probability) or **T** (time).

* **`P`** : Will compare the probability of the target to the value. Only one to handle `?` value.
* **`T`** : Will return the periods of time where the target probability is meeting the criteria of value.
* **`Pmax`** : Will return the highest value of the target probability while meeting the criteria of value.
* **`Pmin`** : Will return the lowest value of the target probability while meeting the criteria of value.
* **`Tmax`** : Will return the last period of time where the target probability is meeting the criteria of value.
* **`Tmin`** : Will return the first period of time where the target probability is meeting the criteria of value.
* **`D`** : Will check if the two nodes passed in parameters are always active at the same time. Names must be separated by commas.
* **`Inc`** : Check if the node or the state passed in parameters sees its probability increase on the last time period after the mutation. Mutation constraints are required.
* **`Dec`** : Check if the node or the state passed in parameters sees its probability decrease on the last time period after the mutation. Mutation constraints are required.

### `[target_type]`

The type of target to look for. Can be **node**, **state** or a **fixpoint**.

* **`node`** : Will look for the probability of the target node.
* **`state`** : Will look for the probability of the target state.

### `[name]`

The name of the target to look for.

* If `target_type` is **node**, name is the name of the node.
* If `target_type` is **state**, name is the name of the state. No spaces or `""`.
* For all targets use `*`.
* Can handle multiple names separated by commas (no spaces or `""` even for multiple names).
* If `target_type` is **state**, you can pass a list of nodes' names if you also put `comb` in the options.

### `[operator]`

The operator to use to compare the target to the value. Can be `<`, `<=`, `=`, `!=`, `>=`, `>` or `/`.

> **Note:** `!=` might return very broad results and `=` might not return anything.

* **`<`** : The probability of the target must be less than the value.
* **`<=`** : The probability of the target must be less than or equal to the value.
* **`=`** : The probability of the target must be equal to the value.
* **`!=`** : The probability of the target must not be equal to the value.
* **`>=`** : The probability of the target must be greater than or equal to the value.
* **`>`** : The probability of the target must be greater than the value.
* **`/`** : Only for query types D, M, Inc and Dec. No value or operator is required.

### `[value]`

The value to compare the target to. Can be a number between 0 and 1, or `?` **ONLY IF** the operator used is `=` and query type is **P**.

* If value is `?`, the query will return the probability of the target.
* With a value of `?`, the logical equation must not be empty.
* The value must be empty for `Dec` or `Inc` types.

### `[logical_equation]` *(Optional)*

An optional logical equation to apply to the results. Can be a string or a list of strings.

* The logical equation is a string that contains the following elements: `[ [name] [operator] [value] ]`
* The operator can be `&`, `|` (pipe). A logical-not `!` can be used in front of a name: `!name`.
* The name can reference a node or a state. By default, the result will be the probability of the node or state, thus returning both. For fewer columns in output, use: `node:name` or `state:name`. To apply a logical-not in this condition, use: `node:!name` or `state:!name`.
* The logical equation can contain a numerical evaluation. This one **must be placed in between parentheses** or strange results may occur.
* The logical equation can have multiple conditions intricate on numerous levels: `[ ( condition A ) | ( ( condition B ) | ( ( condition C ) ) ) ]`
* **Important:** It is really important to separate each member by a space so the parser reads it correctly and does not raise an Exception.

### `[mutations]` *(Optional)*

Optional except for `Inc` and `Dec` operations that compare two simulations of the same model.

* Multiple mutations can be passed. All mutations must be written like: `node_name:ON` or `node_name:OFF`.
* Multiple couples must be separated by a space.

### `[options]`

* **`digits:int`** : Option to restrain the amount of digits after the dot in the computations and output. *e.g., `digits:3` (Default value is 4).*
* **`compare:mut:state,mut2:state`** : Option to compare the computation with this mutation instead of the master simulation. The mutation must be a string like `"node_name:ON"` or `"state_name:OFF"`. Multiple mutations can be passed and must be separated by a comma without spaces.
* **`int%`** : Option to require a minimum difference between the two probabilities of the target. *e.g., `10%` (Default value is 0).*
* **`transient`** : Special option to check for variations during the simulation and not only a difference at the end. It has the following sub-options:
* `threshold:val` : General minimal change value for the evolution comparisons *(Default: 0.05)*
* `start:val` : Minimal change value at the beginning of the simulation *(Default: 0.1)*
* `end:val` : Minimal change value at the end of the simulation *(Default: 0.1)*
* `optimum:val` : Minimal change value to consider reaching a min or max value in the evolution *(Default: 0.1)*
* **`comb`** : Option to combine the probabilities of multiple nodes, will compute the value for both the nodes to be active at the same time. *(Default: False)*



> **Example of options:** `[ 5% digits:2 compare:AKT:OFF,BRAF:ON transient:threshold:0.05,start:0.1,end:0.1 ]`
> *NB: The order of options is not relevant.*

---

## Examples

* `P(node:A) > 0.5`
Returns all the rows where the probability of node A is greater than 0.5.
* `P(node:A,B) < 0.4`
Returns all the rows where the probability of node A and node B is less than 0.4.
* `P(node:A) = ? [ node:B & C ]`
Returns the probabilities of node A to be active in one state while B and C are also active (joint probability).
* `P(state:A) = ? [ ( node:B > 0.3 ) | C ]`
Returns the probabilities of state A to be active in one state while B has a probability greater than 0.3 or while C is active.
* `T(state:A) >= 0.6`
Returns all the periods of time where state A has a probability greater than or equal to 0.6.
* `Tmin(node:A,B) >= 0.3`
Returns the first period of time where node A and node B are active with a probability greater than or equal to 0.3.
* `Tmax(node:A,B) <= 0.7`
Returns the last period of time where node A and node B are active with a probability less than or equal to 0.7.
* `Pmax(node:A) >= 0.5`
Returns the greatest probability of node A being above 0.5 in any period of time. Can return nothing.
* `Pmin(node:A) <= 0.5`
Returns the lowest probability of node A being under 0.5 in any period of time. Can return nothing.
* `Inc(node:A) / [ ] [ B:ON ]`
Returns the last time code comparison and a print saying if the node A was increased or not.
* `Dec(node:A) / [ A & C ] [ B:ON ]`
Returns the last time code comparison and print saying if the node A was decreased or not. The logical equation is applied before the comparison.
* `Inc(state:A--B) / [ ] [ B:ON ]`
Returns the last time code comparison and print saying if the state A--B was increased or not.

---

## Case Studies: Questions and Queries

**Q: What is the probability of node A and B being active at the same time while C is inactive and D above 0.5?**

> `P(node:A,B) = ? [ node:!C & ( D > 0.5 ) ]`

**Q: What are all the moments my simulation is on the state A--B with C inactive?**

> `T(state:A--B) >= 0.0 [ !C ]`

**Q: What probability for the state A--B to be active if C, D or E is active and F is inactive?**

> `P(state:A--B) = ? [ ( C | D | E ) & !F ]`

**Q: When does the probability of state `<nil>` exceeds 0.5?**

> `T(state:<nil>) >= 0.5`

**Q: When does the probability of state `<nil>` exceeds 0.5 for the first time?**

> `Tmin(state:<nil>) >= 0.5`

**Q: When does the probability of state `<nil>` exceeds 0.5 for the last time?**

> `Tmax(state:<nil>) >= 0.5`

**Q: Does the probability for A--B state increase when C is activated?**

> `Inc(state:A--B) / [ ] [ C:ON ]`

---

## Additional Info & Contact

For more examples and output examples, you can check the `test_evaluator.py` file. Check the notebook *Tuto Temporal Logic* for more info.

In case of any question or bug, you can contact me at:

* **Email** : oscardufossez@gmail.com
* **GitHub** : [ODufossez](https://www.google.com/search?q=https://github.com/ODufossez)