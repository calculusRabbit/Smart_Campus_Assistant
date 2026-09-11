#!/bin/bash                                                                   
#SBATCH --job-name=llm_judge                                                
#SBATCH --nodes=1                                                             
#SBATCH --ntasks=1                                                            
#SBATCH --gres=gpu:4                                      
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G                           
#SBATCH --time=10:00:00                 
source ~/data/nlp_env/bin/activate                                            
cd ~/data/WSU_senior_design_project_2026/services/rag
python -m processing.llm_judge