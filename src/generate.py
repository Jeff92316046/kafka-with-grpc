import os

proto_path = "src/protos"
output_dir = "src/generated"
proto_target = 'src/protos/message.proto'

# generate the python files from the proto files
os.system(
    "python -m grpc_tools.protoc "
    f"    --proto_path={proto_path} "
    f"    --python_out={output_dir} "
    f"    --grpc_python_out={output_dir} "
    f"    --pyi_out={output_dir} "
    f"    {proto_target}"
)
