from core.template_renderer import render

def build_project(config):
    files = {}

    # ROOT
    for file in ["main.tf", "variables.tf", "outputs.tf", "provider.tf"]:
        path = f"root/{file}.j2"
        files[file] = render(path, config.dict())

    # MODULE network
    for file in ["vpc.tf", "security.tf", "variables.tf", "outputs.tf"]:
        path = f"modules/network/{file}.j2"
        files[f"modules/network/{file}"] = render(path, config.dict())

    # MODULE ec2
    for file in ["ec2.tf", "variables.tf", "outputs.tf"]:
        path = f"modules/ec2/{file}.j2"
        files[f"modules/ec2/{file}"] = render(path, config.dict())

    return files
