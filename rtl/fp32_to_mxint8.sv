// quantizes a post-ReLU fp32 activation to a microscaled mxint8 value based on its shared block exponent 

`default_nettype none

module fp32_to_mxint8 #(
    parameter int EXP_W = 8
)(

    input logic [31:0] fp32,
    input logic [EXP_W-1:0] block_e, // block scale exp; will always be >= the element's exponent, since the significant is already < 2. 

    output logic signed [7:0] mxint8
);
    /*  
        for readme at some point: 
        the fp value we're shifting is the mantissa {1, frac} (24-bit int) * 2^-23 (to get mantissa to 1.frac), multiplied by 2^(E-127). 
        So val_fp = {1, f} * 2^(E - 127 - 23) = {1, f} * 2^(E - 150)
        to microscale this value with its (biased) block exponent e, we then divide val_fp by 2^(e - 127), or multiply by 2^-(e - 127). 
        we then quantize our value, which is now in the range (-1.95, 1.95), to int8 by multiplying by 2^6. (to Q2.6)
        this is val_fp * 2^-e * 2^6 --> {1, f} * 2^(E - 150) * 2^(127 - e + 6) --> {1, f} * 2^(E - e - 17)
        to get in terms of a right shift: {1, f} * 2^-(17 + e - E) or a right shift of 17 + e - E. 
        note that since e >= E, we'll always shift rightward at least 17 bits.
        Since we're shifting a 24 bit value, the fractional bits of the result will be at the 25th bit from the msb, and 
        the integer value we want is in the 8 bits above the decimal place.
    */
    logic [7:0]  fp_E;
    logic [8:0] shift_amt; 
    logic [23:0] significand;
    logic [23:-1] shifted; 
    logic negative;
    logic [7:0] mag; // 

    always_comb begin : quantize

        fp_E = fp32[30:23]; // fp exponent bits
        significand = { 1'b1, fp32[22:0] }; // fp significant as 24 bit uint, 1.frac_bits * 2^-23
        shift_amt = 9'd17 + block_e - fp_E; // max value is 17 + 254 - 1 = 270, needs 9 bits
        shifted = { significand, 1'b0 } >> shift_amt; // extra bit to shift first frac bit into
        negative = fp32[31];


        // unsigned magnitude, round half up. by always shifting at least 17 bits, the raw value is always < 128 (shifted[7] = 0)
        mag = ( shifted[-1] == 1 ) ? shifted[7:0] + 8'd1 : shifted[7:0];  

        // output is zero for any subnormal values (fp exp == x00) 
        if ( fp_E == 8'h00 ) mxint8 = 8'h00;
        // saturate if we rounded to 128 (symmetric, |127| max for pos and neg)
        else if ( mag > 8'd127 ) mxint8 =  negative ? 8'h81 : 8'h7F;
        // standard case 
        else mxint8 = negative ? ~mag + 8'b1 : mag;
    

    end


endmodule