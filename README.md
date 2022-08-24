Create conf/config.yaml, the example  content is as follows:

```yaml
data:
  photos: data/photos/
  annotations: data/annotations/
  output_annotation: data/output/annotations/
  output_photos: data/output/photos/
  required_bbch_codes: [71,73]
voc_transformer:
  source_annotations_path: data/output/annotations/
  target_annotation_path: data/output/annotations/json/
stats:
  xml_directory_path: data/output/annotations/
```