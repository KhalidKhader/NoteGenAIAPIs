You make the following common mistakes: 
1- when using AWS Commands use 
`|cat` to ensure you don't get into new line issues with commands. 

2- AWS is source of truth. use aws cli (with notegen profile, canada region), to consult as src of truth.  

3- don't run terraform apply on your own. check with me first.

4- terraform is used for 1 time / infra build 

5- github workflow / actions and task definitions under aws is what is used for code deployment. 

6- When working with AWS and configuring applications secrets should go to secrets manager, non-secrets go to param store. 

7- keep any configs that are timeouts, etc. in task definition to allow dev to optimize or change these, such as logging level. 