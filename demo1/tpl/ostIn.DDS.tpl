# Ostrich configuration file

ProgramType  DDS
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

BeginDDSAlg
PerturbationValue 0.20
MaxIterations 3
#UseRandomParamValues
UseInitialParamValues
EndDDSAlg
