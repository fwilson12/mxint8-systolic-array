
`timescale 1ns/1ps
`default_nettype none

module array #(

    parameter int COLS = 4,
    parameter int ROWS = 4,
    parameter int W = 8,
    parameter int PSUM_W = 17

)(
    input logic rst,
    input logic clk,

    // from north
    input logic signed [W-1:0] weight_in     [COLS-1:0],
    input logic                accept_weight [COLS-1:0], // colummn-wide

    // from west
    input logic signed [W-1:0] activation_in  [ROWS-1:0],
    input logic                act_valid_in   [ROWS-1:0],
    input logic                weight_swap_in [ROWS-1:0],
    input logic                pe_enabled,    // array-wide


    // to south
    output logic signed [PSUM_W-1:0] pe_psum_out [COLS-1:0], 
    output logic                     valid_out   [COLS-1:0]

);

    // net grids

    // north -> south signals, need extra row above 
    logic signed [PSUM_W-1:0] psums   [0:ROWS][0:COLS-1];
    logic signed [W-1:0]      weights [0:ROWS][0:COLS-1];

    // west -> east signals, need extra col to the left
    logic signed [W-1:0]   activations [0:ROWS-1][0:COLS];
    logic                  a_valid     [0:ROWS-1][0:COLS];
    logic                  w_swap      [0:ROWS-1][0:COLS];

    
    // init net grids

    genvar row, col;

    generate

        for ( col = 0; col < COLS; col=col+1 ) begin : row0
            assign psums[0][col] = 'b0;
            assign weights[0][col] = $signed( weight_in[col] );
        end

        for ( row = 0; row < ROWS; row=row+1 ) begin : col0
            assign activations[row][0] = $signed( activation_in[row] );
            assign a_valid[row][0] = act_valid_in[row];
            assign w_swap[row][0] = weight_swap_in[row];
        end



        // init array

        for ( row = 0; row < ROWS; row=row+1 ) begin : aRows
            for ( col = 0; col < COLS; col=col+1 ) begin : aCols

                pe #(.W(W), .PSUM_W(PSUM_W)) u_pe (
                    
                    .clk( clk ),
                    .rst( rst ),

                    // north
                    .psum_in( psums[row][col] ),
                    .weight_in( weights[row][col] ),
                    .accept_weight( accept_weight[col]),

                    // west
                    .activation_in( activations[row][col] ),
                    .act_valid_in( a_valid[row][col] ),
                    .weight_swap_in( w_swap[row][col] ),
                    .pe_enabled( pe_enabled ),

                    // south
                    .psum_out( psums[row+1][col] ),
                    .weight_out( weights[row+1][col] ),

                    // east
                    .activation_out( activations[row][col+1] ),
                    .act_valid_out( a_valid[row][col+1] ),
                    .weight_swap_out( w_swap[row][col+1] )
                );
            end
        end

        // assign output

        for ( col = 0; col < COLS; col=col+1 ) begin : outputs
            assign pe_psum_out[col] = psums[ROWS][col];
            assign valid_out[col] = a_valid[ROWS - 1][col + 1]; // want valid signal that was just in this PE (1 col to the right)
        end


    endgenerate


endmodule

