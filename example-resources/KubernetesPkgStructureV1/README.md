# Resource
Example Kubernetes package structure for a Resource which will have the following behaviour:

On Create:
    Create a some ConfigMaps/Secrets
On Install:
    Create a deployment
    Wait for the deployment to be ready
    Get some outputs from the deployment

On operation named AddToDispatchList:
    Create a job 
    Wait for the job to complete

On operation named RemoveFromDispatchList:
    Create a job 
    Wait for the job to complete

On operation named StartTrafficTest
    Install a Helm chart

On operation named StopTrafficTest
    Uninstall a Helm chart

On Uninstall:
   Remove deployment

On Delete:
   Remove ConfigMap/Secrets


# Bag of bits explained

Look at keg.yaml first.

keg.yaml - entry point file. Driver uses this to determine when objects/helm charts are created/deleted
objects - Kubernetes object yaml files (referenced in keg.yaml)
helm - Helm charts and values files (referenced in keg.yaml)
scripts - optional "-ready" (to check things are ready) and "-output" (to get outputs) scripts for each Transition/Operation

(We could include the scripts in keg.yaml, as multiline strings but I assumed most people would prefer separate files with a .py extension so they can use IDE syntax highlighting)

So on every transition the Kubedriver will:
- Create/Delete any objects set out in keg.yaml
- Install/Uninstall any objects set out in keg.yaml
- If included, run the {transition-name}-ready.py script
- If included, run the {transition-name}-outputs.py script