import math
import sys
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
    return abs(part_val - proposed_val)

#produces a cost function that weights additions as 1 and removals as base^weight
def exp_weight_cost_fun(base, weight):
    return lambda part, proposed: proposed - part if part <= proposed else math.pow(base,weight)*(part - proposed)

#get the decimal value of a bitstring, or None if the string is invalid (starts with a 0 and has other digits)
def get_bit_value(bits):
    if len(bits) < 1 or (bits[0] == '0' and len(bits) > 1):
        value = None
    else:
        value = binaryStringToDec(bits)[0]
    return value

def est_area_multiplier(num_additions, area_remaining):
    min_area_per_blob = 500
    if area_remaining < num_additions*min_area_per_blob:
        return 100000
    else:
        return 1

#for the given part structure (part_vals), target bitstring, and cost function,
#find the divisions of the target that produce the lowest cost when compared to part_vals
#output of the form [cost_value, [list of part values], [list of divider posns (divider comes after the posn)]]
def find_divisions(part_vals, bitstring, cost_fun, multipliers=None, areas_remaining=None):
    num_dividers = len(part_vals) - 1
    num_posns = len(bitstring) - 1
    costs = [[None for _ in range(num_posns)] for _ in range(num_dividers)]
    if multipliers is None:
        multipliers = [1.0 for _ in range(num_dividers+1)]

    #only 0 or 1 parts given
    if num_dividers <= 0:
        bit_val = get_bit_value(bitstring)
        if num_dividers == 0 and bit_val is not None:
            if areas_remaining is not None:
                area_multiplier = est_area_multiplier(bit_val-part_vals[0],areas_remaining[0])
            else:
                area_multiplier = 1
            return [cost_fun(part_vals[0],bit_val)*multipliers[0]*area_multiplier, [bit_val], []]
        else:
            return None

    #initialize first column of costs
    for i in range(num_posns):
        if num_dividers > 1:
            bit_val = get_bit_value(bitstring[:(i+1)])
            if bit_val is not None:
                if areas_remaining is not None:
                    area_multiplier = est_area_multiplier(bit_val-part_vals[0],areas_remaining[0])
                else:
                    area_multiplier = 1
                costs[0][i] = [cost_fun(part_vals[0],bit_val)*multipliers[0]*area_multiplier, [bit_val], [i]]
            else:
                costs[0][i] = None
        else: #special case if there is only 1 divider
            bit_val_1 = get_bit_value(bitstring[:(i+1)])
            bit_val_2 = get_bit_value(bitstring[(i+1):])
            if bit_val_1 is not None and bit_val_2 is not None:
                if areas_remaining is not None:
                    area_multiplier_1 = est_area_multiplier(bit_val_1-part_vals[0],areas_remaining[0])
                    area_multiplier_2 = est_area_multiplier(bit_val_2-part_vals[1],areas_remaining[1])
                else:
                    area_multiplier_1 = 1
                    area_multiplier_2 = 1
                cost_1 = cost_fun(part_vals[0],bit_val_1)*multipliers[0]*area_multiplier_1
                cost_2 = cost_fun(part_vals[1],bit_val_2)*multipliers[1]*area_multiplier_2
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
                        if areas_remaining is not None:
                            area_multiplier = est_area_multiplier(bit_val-part_vals[i],areas_remaining[i])
                        else:
                            area_multiplier = 1
                        extend_cost = cost_fun(part_vals[i],bit_val)*multipliers[i]*area_multiplier
                    else:
                        extend_cost = None
                    bit_val = [bit_val]
                else:
                    bit_val_1 = get_bit_value(bitstring[k+1:j+1])
                    bit_val_2 = get_bit_value(bitstring[j+1:])
                    if bit_val_1 is not None and bit_val_2 is not None:
                        if areas_remaining is not None:
                            area_multiplier_1 = est_area_multiplier(bit_val_1-part_vals[i],areas_remaining[i])
                            area_multiplier_2 = est_area_multiplier(bit_val_2-part_vals[i+1],areas_remaining[i+1])
                        else:
                            area_multiplier_1 = 1
                            area_multiplier_2 = 1
                        extend_cost_1 = cost_fun(part_vals[i],bit_val_1)*multipliers[i]*area_multiplier_1
                        extend_cost_2 = cost_fun(part_vals[i+1],bit_val_2)*multipliers[i+1]*area_multiplier_2
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
        return ((sys.maxint>>1)+len(part_vals), None, None)


if __name__ == '__main__':
    import time
    start = time.time()
    for i in range(200):
        test_parts = [1,3,0,4,0,5,9,0,0,1,3,6,8,1,4,1,0,3,5,2]#[1,3,0,4,0,5,9,0,0,1,3,6,8,1,4,1,0]
        test_bits = '1110010110110011001110101101101111'#'11001110110001010110000010101'
        print find_divisions(test_parts,test_bits,abs_diff_cost)
    print time.time() - start