from conversions import *

#finds the absolute difference between values in the same position of 2 lists
#not used for find_divisions, but maybe useful for testing?
def list_abs_diff_cost(part_vals, proposed_vals):
    if len(part_vals) != len(proposed_vals):
        cost = -1
        print('ERROR: Cannot calculate cost for lists of different lengths')
    else:
        cost = 0
        for i in range(len(part_vals)):
            cost += abs_diff_cost(part_vals[i],proposed_vals[i])
    return cost

#cost function that just takes the absolute difference between two values
def abs_diff_cost(part_val, proposed_val):
    return abs(part_val-proposed_val)

#get the decimal value of a bitstring, or None if the string is invalid (starts with a 0 and has other digits)
def get_bit_value(bits):
    if len(bits) < 1 or (bits[0] == '0' and len(bits) > 1):
        value = None
    else:
        value = binaryStringToDec(bits)[0]
    return value

#for the given part structure (part_vals), target bitstring, and cost function,
#find the divisions of the target that produce the lowest cost when compared to part_vals
#output of the form [cost_value, [list of part values], [list of divider posns (divider comes after the posn)]]
def find_divisions(part_vals, bitstring, cost_fun):
    num_dividers = len(part_vals) - 1
    num_posns = len(bitstring) - 1
    costs = [[None for _ in range(num_posns)] for _ in range(num_dividers)]

    #only 0 or 1 parts given
    if num_dividers <= 0:
        bit_val = get_bit_value(bitstring)
        if num_dividers == 0 and bit_val is not None:
            return [cost_fun(part_vals[0],bit_val), [bit_val], []]
        else:
            return None

    #initialize first column of costs
    for i in range(num_posns):
        if num_dividers > 1:
            bit_val = get_bit_value(bitstring[:(i+1)])
            if bit_val is not None:
                costs[0][i] = [cost_fun(part_vals[0],bit_val), [bit_val], [i]]
            else:
                costs[0][i] = None
        else: #special case if there is only 1 divider
            bit_val_1 = get_bit_value(bitstring[:(i+1)])
            bit_val_2 = get_bit_value(bitstring[(i+1):])
            if bit_val_1 is not None and bit_val_2 is not None:
                cost_1 = cost_fun(part_vals[0],bit_val_1)
                cost_2 = cost_fun(part_vals[1],bit_val_2)
                costs[0][i] = [cost_1+cost_2, [bit_val_1,bit_val_2], [i]]

    #fill all other columns of costs
    for i in range(1,num_dividers):
        for j in range(i,num_posns):
            possible_costs = []
            for k in range(j):
                prev_cost = costs[i-1][k]
                if i < num_dividers-1:
                    bit_val = get_bit_value(bitstring[k+1:j+1])
                    if bit_val is not None:
                        extend_cost = cost_fun(part_vals[i],bit_val)
                    else:
                        extend_cost = None
                    bit_val = [bit_val]
                else:
                    bit_val_1 = get_bit_value(bitstring[k+1:j+1])
                    bit_val_2 = get_bit_value(bitstring[j+1:])
                    if bit_val_1 is not None and bit_val_2 is not None:
                        extend_cost_1 = cost_fun(part_vals[i],bit_val_1)
                        extend_cost_2 = cost_fun(part_vals[i+1],bit_val_2)
                        extend_cost = extend_cost_1 + extend_cost_2
                    else:
                        extend_cost = None
                    bit_val = [bit_val_1, bit_val_2]
                if prev_cost is not None and extend_cost is not None:
                    possible_costs.append([prev_cost[0]+extend_cost, prev_cost[1]+bit_val, prev_cost[2]+[j]])
            if possible_costs:
                costs[i][j] = min(possible_costs)
            else:
                costs[i][j] = None

    #find best case for all dividers being chosen
    ans = []
    for val in costs[num_dividers-1]:
        if val is not None:
            ans.append(val)
    if ans:
        return min(ans)
    else:
        return None


if __name__ == '__main__':
    test_parts = [1,3,0,4,0,5,9,0,0,1,3,6,8,1,4,1,0]
    test_bits = '11001110110001010110000010101'
    print find_divisions(test_parts,test_bits,abs_diff_cost)