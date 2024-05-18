import torch

# Check if CUDA is available
cuda_available = torch.cuda.is_available()
print(f"CUDA Available: {cuda_available}")

if cuda_available:
    # Print the CUDA version PyTorch was built with
    print(f"PyTorch CUDA Version: {torch.version.cuda}")
    
    # If you have a CUDA GPU, print the current GPU name and its compute capability
    gpu_name = torch.cuda.get_device_name(0)
    compute_capability = torch.cuda.get_device_capability(0)
    print(f"GPU Name: {gpu_name}, Compute Capability: {compute_capability}")
else:
    print("CUDA is not available. Check if you have a CUDA-capable GPU and the correct version of PyTorch installed.")

print("Current Version of pytorch installed: ")
print(torch.version)

print("Current Version of cuda + torch installed: ")
print(torch.version.cuda)