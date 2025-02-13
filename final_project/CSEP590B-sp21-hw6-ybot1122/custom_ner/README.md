## for personal reference; 

Annotation
```
docker pull doccano/doccano   
docker container create --name doccano \
  -e "ADMIN_USERNAME=admin" \
  -e "ADMIN_EMAIL=admin@example.com" \
  -e "ADMIN_PASSWORD=password" \
  -p 8000:8000 doccano/doccano
```

Next, start doccano by running the container:

`docker container start doccano`

To stop the container, run `docker container stop doccano -t 5`. All data created in the container will persist across restarts.

run `python3 convert_data_to_jsonl.py` to receive a JSONL file named `spacey20.jsonl` which can be dropped into Doccano


Training
1. Create config (should not be needed): `python3 -m spacy init fill-config base_config.cfg config.cfg`
2. Save the output of Doccano as `admin.jsonl` and run `python3 convert_spacy.py` which will convert the spacey2.0 file to a compatible spacey file for 3.0
3. `train.spacy` for training, and `dev.spacy` for validation
4. Run training `python3  -m spacy train config.cfg --paths.train ./train.spacy --paths.dev ./dev.spacy --output ./output`

