FROM blender:4.2.0

WORKDIR /worker

COPY backend/app/reconstruction/blender/scripts /worker/scripts

ENV PYTHONUNBUFFERED=1
ENV BLENDER_SCRIPT=/worker/scripts/reconstruct.py

# Worker runtime entrypoint can be overridden by orchestration platform.
CMD ["blender", "--background", "--python", "/worker/scripts/reconstruct.py"]
