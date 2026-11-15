import prefect, pkgutil, sys
print('Prefect version:', prefect.__version__)
for _, modname, ispkg in pkgutil.iter_modules(prefect.__path__):
    if 'tasks' in modname:
        print('Prefect submodule:', modname)

