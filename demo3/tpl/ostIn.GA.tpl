# Ostrich configuration file

ProgramType  GeneticAlgorithm
ModelExecutable ./run_trial.sh
ObjectiveFunction gcop

OstrichWarmStart no

PreserveModelOutput ./save_model_output.sh
PreserveBestModel ./save_best.sh
OnObsError	-999

BeginFilePairs    
EndFilePairs

#Parameter/DV Specification
BeginParams
    #parameter	init	lwr	upr	txInN  txOst 	txOut fmt  
EndParams

BeginResponseVars
  #name	  filename					keyword		line	col	token
  KGE      ./trial_stats.txt;		OST_NULL	0		1  	 ' '
EndResponseVars 

BeginTiedRespVars
  NegKGE 1 KGE wsum -1.00
EndTiedRespVars

BeginGCOP
  CostFunction NegKGE
  PenaltyFunction APM
EndGCOP

BeginConstraints
# not needed when no constraints, but PenaltyFunction statement above is required
# name     type     penalty    lwr   upr   resp.var
EndConstraints

# Randomsed control added
RandomSeed xxxxxxxxx

BeginGeneticAlg
ParallelMethod synchronous 
PopulationSize 50 
MutationRate 0.05 
Survivors 1 
NumGenerations 50 
InitPopulationMethod LHS 
ConvergenceVal 1.00E-4 
EndGeneticAlg
