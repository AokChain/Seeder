from webargs import fields

filter_args = {
    "after": fields.Int(missing=None, validate=lambda v: v > 0)
}
