using TensorQEC

dem2 = TensorQEC.parse_dem_file(joinpath(@__DIR__, "dem", "dem_T1_err-2.7.dem"))

tanner = TensorQEC.dem2tanner(dem2)
decoder = IPDecoder()
em = IndependentFlipError{Float64}(dem2.error_rates)
ct = compile(decoder,TensorQEC.get_problem(tanner,em))
logical_pos = findall(x-> dem2.logical_list[1] ∈ x ,dem2.flipped_detectors)

num = 1
count = 0 
while count < 500
    global count
    global num
    if num % 100 == 0
        @show num count count/num
    end
    error_pattern =  random_error_pattern(em)
    syd = syndrome_extraction(error_pattern, tanner)

    res = decode(ct,syd)
    @assert syd == syndrome_extraction(res.error_pattern, tanner)

    num += 1

    if sum((error_pattern+res.error_pattern)[logical_pos]).x
        count += 1
        @show num count count/num
    end
end