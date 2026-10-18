

`timescale 1ns/1ps


module pe #(
    parameter int W      = 8,
    parameter int PSUM_W = 17   // 4 MACs of (-127 * -127) needs 17 bits signed
)(

    input logic clk,
    input logic rst,

    // from north
    input logic signed  [PSUM_W-1:0] psum_in,
    input logic signed  [W-1:0] weight_in,
    input logic                 accept_weight, // colummn-wide

    // from west
    input logic signed [W-1:0] activation_in,
    input logic                act_valid_in,
    input logic                weight_swap_in,
    input logic                pe_enabled,    // array-wide
    
    // to south
    output logic signed [PSUM_W-1:0] psum_out,
    output logic signed [W-1:0] weight_out,
    
    // to east
    output logic signed [W-1:0] activation_out,
    output logic                act_valid_out,
    output logic                weight_swap_out
);

    // weight registers
    logic signed [W-1:0] weight_active;
    logic signed [W-1:0] weight_shadow;

    // activation/psum registers
    logic signed [W-1:0]      activation;
    logic signed [PSUM_W-1:0] psum;

    // status registers
    logic valid;
    logic swap;

    

    always_ff @( posedge clk or posedge rst ) begin
        
        if ( rst ) begin
            activation <= '0;
            psum <= '0;
            weight_active <= '0;
            valid <= '0;
            swap <= '0;
            weight_shadow <= '0;
        end

        else begin
            if ( pe_enabled ) begin

                // multiply-accumulate
                if ( act_valid_in ) psum <= psum_in + weight_active * activation_in;
                
                // incoming bubble, ignore the mul
                else psum <= psum_in;

                // update registers
                if ( accept_weight ) weight_shadow <= weight_in;
                if ( weight_swap_in ) weight_active <= weight_shadow;

                // standard transparencies 
                activation <= activation_in;
                valid <= act_valid_in;
                swap <= weight_swap_in;
            end

            // pe disabled - freeze
            else begin
                psum <= psum;
                activation <= activation;
                valid <= valid;
                swap <= swap;
                weight_active <= weight_active;
                weight_shadow <= weight_shadow;
            end
        end
    end

    // output
    assign psum_out = psum;
    assign weight_out = weight_shadow;
    assign activation_out = activation;
    assign act_valid_out = valid;
    assign weight_swap_out = swap;


endmodule
