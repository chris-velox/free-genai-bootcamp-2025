# Running Multiple OPEA Comps on MacOS using Docker Desktop

## Prerequisites

- Docker Desktop
- OPEA Comps

## Steps

1. Open Docker Desktop
    - The starts the Docker engine on the Mac
    - Make sure the `docker context` is pointing to the correct Docker engine
        - Best to use the unprivileged docker engine with Docker Desktop, so the Docker Endpoint will look like this: `unix:///Users/<username>/.docker/run/docker.sock`

### Create docker-compose.yml

```yaml
services:
  ollama-server:
    image: ollama/ollama
    container_name: ollama-server
    ports:
      - ${LLM_ENDPOINT_PORT:-8008}:11434
    environment:
      no_proxy: ${no_proxy}
      http_proxy: ${http_proxy}
      https_proxy: ${https_proxy}
      LLM_MODEL_ID: ${LLM_MODEL_ID}
      host_ip: ${host_ip}

networks:
  default:
    driver: bridge
```

```sh
LLM_ENDPOINT_PORT=8008 host_ip=`ipconfig getifaddr en1` LLM_MODEL_ID="llama3.2:1b" docker compose up
```

### Install a model in server

*If this isn't done, the ollama-server reports there are no models.*

From [ollama GitHub page](https://github.com/ollama/ollama/blob/main/docs/docker.md) about Docker.

Message when there are no models:

```error
curl http://localhost:8008/api/ps
{"models":[]}%
```

Install the `llama3.2:1b` model in ollama-server:

```sh
docker exec -it ollama-server ollama run llama3.2:1b
```

Response:

```text
pulling manifest
pulling 74701a8c35f6... 100% ▕████████████████████████████████████████████████████████▏ 1.3 GB
pulling 966de95ca8a6... 100% ▕████████████████████████████████████████████████████████▏ 1.4 KB
pulling fcc5a6bec9da... 100% ▕████████████████████████████████████████████████████████▏ 7.7 KB
pulling a70ff7e570d9... 100% ▕████████████████████████████████████████████████████████▏ 6.0 KB
pulling 4f659a1e86d7... 100% ▕████████████████████████████████████████████████████████▏  485 B
verifying sha256 digest
writing manifest
success
>>> Send a message (/? for help)
```

**Correct** response after installing the model to ollama-server:

```text
curl http://localhost:8008/api/ps
{"models":[{"name":"llama3.2:1b","model":"llama3.2:1b","size":2233526272,"digest":"baf6a787fdffd633537aa2eb51cfd54cb93ff08e28040095462bb63daf552878","details":{"parent_model":"","format":"gguf","family":"llama","families":["llama"],"parameter_size":"1.2B","quantization_level":"Q8_0"},"expires_at":"2025-02-16T20:08:45.193838343Z","size_vram":0}]}% 
```

### Test to see if Llama is working

```text
>>> why is the sky blue?
The sky appears blue to us because of a phenomenon called Rayleigh scattering, named after the British physicist
Lord Rayleigh. He discovered that when sunlight enters Earth's atmosphere, it encounters tiny molecules of gases
such as nitrogen and oxygen.

These gas molecules are much smaller than the wavelength of light, which is the distance between two consecutive
peaks or troughs in a wave. As a result, these small molecules scatter the shorter (blue) wavelengths of light
more efficiently than the longer (red) wavelengths.

This scattering effect gives the sky its blue color. The amount of scattering that occurs depends on the altitude
at which the light reaches us and the concentration of atmospheric gases. At higher altitudes, where the air is
thinner, more blue light is scattered, making the sky appear bluer. Conversely, at lower altitudes, more red light
is scattered, giving the sky a reddish hue.

It's worth noting that during sunrise and sunset, the angle of the sunlight is such that it hits the atmosphere at
an angle, which causes even more scattering of shorter wavelengths (like blue and violet). This is why these times
of day can produce spectacular displays of colorful light in the sky.
```

### Try using the API

```sh
curl --noproxy "*" http://localhost:8008/api/generate -d '{
  "model": "llama3.2:1b",
  "prompt":"Why is the sky blue?"
}'
```

It should return the same text in chunks as the direct query in the prompt.

### Pull a model using the API

```sh
curl --noproxy "*" http://localhost:8008/api/pull -d '{
  "model": "gemma:2b"
}'
```

Test the model with docker exec

```sh
docker exec -it ollama-server ollama run gemma:2b
```

Response:

```text
>>> why is the sky blue?
The sky appears blue due to a phenomenon called **Rayleigh scattering**. This scattering process involves the
interaction of light with molecules in the Earth's atmosphere. Here's a breakdown of the process:

1. **Sun's light:** The sun emits all colors of the spectrum (red, orange, yellow, green, blue, indigo, and
violet), each with different wavelengths having varying amounts of energy.
2. **Atmosphere:** As sunlight enters Earth's atmosphere, it interacts with the molecules of different gases.
3. **Scattering:** The blue and violet light have shorter wavelengths and higher energy compared to the longer
wavelengths like red and orange.
4. **Scattering pattern:** These shorter blue and violet light waves are scattered more efficiently than the
longer red and orange light.
5. **Blue light dominant:** This scattering pattern results in a higher concentration of blue and violet light in
the sky, giving us the perception of a blue color.

Therefore, the blue color of the sky is a result of Rayleigh scattering, which is why the sky appears blue.
```

Test the model with API:

```sh
curl --noproxy "*" http://localhost:8008/api/generate -d '{                                         49s free-genai-bootcamp-2025
  "model": "gemma:2b",   
  "prompt":"Why is the sky blue?"
}'
```

## Technical Uncertainty

How to get a model running on a late-2013 iMac without a big GPU? Use Docker with small language models, like Llama 3.2 (1b) and Gemma (2b) will work, but they are not fast.

Will it run? Small language models in the 0.5-2 billion parameter range seem to run. I have tried a 7 billion parameter model before the bootcamp and my iMac went out to lunch.

Can we run it using Docker Desktop in a container? Yes! In fact, we can run multiple models within the same container.

Once it's running, how can we connect to it? We can connect directly to the language model using the API (/api/generate -d {payload}) or `docker exec -it` commands.

How can we get a front-end for it to hide the API calls?

Can we pull multiple models? Yes, we can pull models either through the API (/api/pull -d) or using `docker exec -it` commands.

## Models

Need to use small models because of system limitations.

- [Llama3.2:1b](https://ollama.com/library/llama3.2:1b)
- [gemma:2b](https://ollama.com/library/gemma:2b)

## Notes

Gemma:2b was much faster than Llama3.2:1b using the API, and was more concise.
