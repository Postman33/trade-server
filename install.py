import os
import pkg_resources

# Создание requirements.txt
requirements = []
for dist in pkg_resources.working_set:
    requirements.append(f"{dist.project_name}=={dist.version}")

with open('requirements.txt', 'w') as file:
    file.write('\n'.join(requirements))