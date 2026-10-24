import random   
import math

import struct


BLOCK_SIZE = 16
LOW_BOUND = -127 # while the minimum value in Q2.6 is -2, for symmetry we saturate both positive and negative magnitudes to 127
UPPER_BOUND = 127

EXP_BIAS = 127
FRAC_BITS = 6

# hardware uses fp32, but the default in python is fp64. used locally only in golden model
def to_fp32(x: float) -> float:
    # compress x to a 4-byte ieee fp32, read the compressed fp32 back as a python float64
    return struct.unpack('f', struct.pack('f', x))[0]

# turn python fp64 into the 32-bit fp32 string the hardware expects. used for cocotb driver 
def fp32_bits(x: float):
    # compress py fp64 to 4-byte fp32, read as uint32
    return struct.unpack('I', struct.pack('f', x))[0]

def getE(vector: list[float]) -> int:
    # find & return the microscaled block (biased) exponent of a block of integers

    bigNum = max(abs(comp) for comp in vector) # avoid unnecessary calculations

    # prevent taking the log of 0 if we see an all-zero block, which should theoretically never happen
    if bigNum == 0: raise ValueError("All zero block!")

    # stores the block exponent, determined by the greatest power of two we can divide each value by : the quantized block values are within (-1.98, ~1.98)
    bigE = math.floor(math.log2(bigNum))

    return min(bigE + EXP_BIAS, 255) # exponents stored in u_int8 format


def quantize(vector: list[float], exp: int) -> list[int]:
    # scale each block | note: exp is biased w/ 127

    # convert float values in a block into their microscaled values; a value between +- ~1.98 represented as an 8 bit Q2.6 
    # value, which the hardware treats like plain int8s (1.98 = x7F = 127, -1.98 = x81 = -127)
    mxBlock = []
    for num in vector:
        scaled = num / 2**(exp - EXP_BIAS) * 2**FRAC_BITS
        mag = min(math.floor(abs(scaled) + 0.5), UPPER_BOUND)   # round half up, saturate
        mxBlock.append(-mag if scaled < 0 else mag)
    return mxBlock    # note: values won't be greater than 127 due to the way the block exponent is calculated, but values below -127 saturate to mimic hardware int8 clamping  



def mxDotProd(wBlock: list[int], aBlock: list[int], eW: int, eA: int) -> int:
    # calculate the dot product of a weight and activation block 

    unscaledProd = sum([weight * activation for weight, activation in zip(wBlock, aBlock)])

    return unscaledProd * 2**(eW + eA - 2*EXP_BIAS - 2*FRAC_BITS) 



def mxint8test(wBlock: list[int], aBlock: list[int]) -> int:
    # microscale and quantize blocks, calculate their dot prod and return unscaled result

    eW = getE(wBlock)
    eA = getE(aBlock)

    print(f"\nWeight Scale: {eW - 127} | Activation Scale: {eA - 127}\n")

    f_wBlock = quantize(wBlock, eW)
    f_aBlock = quantize(aBlock, eA)


    print(f"Quantized Weights: {f_wBlock}\nQuantized Activations: {f_aBlock} \n\n")

    mx_test = mxDotProd(f_wBlock, f_aBlock, eA, eW)

    return mx_test


def refTest(weights: list[float], acts: list[float]) -> float:
    # standard float dot product for comparison
    prod = sum([w * a for w, a in zip(weights, acts)])

    return prod



def random_test():
    # generate random weight & activation blocks, microscale and quantize, calculate their unscaled dot product, and compare to full-precision reference
    weights = []
    acts = []

    for _ in range(BLOCK_SIZE):
        weights.append(to_fp32(random.gauss(0, 5 * random.random())))
        acts.append(to_fp32(random.gauss(0, 1)))


    # print(f"Raw Weights: {weights} \nRaw Activations: {acts}\n\n")

    mx_res = mxint8test(weights, acts)
    print(f"mxint8 result: {mx_res}\n")

    ref_res = refTest(weights, acts)
    print(f"expected result: {ref_res}\n")


    # use abs for normalized error analysis
    weights = [abs(w) for w in weights]
    acts = [abs(a) for a in acts]
    ref_mag = refTest(weights, acts)
    print(f"Error: {(mx_res - ref_res) / ref_mag * 100}% | Absolute error: {mx_res - ref_res}")


if __name__ == '__main__':
    random_test()

