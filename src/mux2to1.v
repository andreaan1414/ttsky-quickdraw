module mux2to1(
    input        s,
    input  [3:0] i0,
    input  [3:0] i1,
    output [3:0] y
);
    assign y = (~{4{s}} & i0) | ({4{s}} & i1);
endmodule
