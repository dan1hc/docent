from .. import constants
from .. import enums
from .. import objects


class HealthzNameSpaceConstants(constants.FrameworkConstants):
    """Constant values specific to all healthz methods."""

    BASE_RESPONSE_HEADERS: objects.response.Headers = (
        objects.response.Headers.from_list(
            [
                objects.response.Header(
                    header.value,
                    description=(
                        enums.header.DefaultHeaderValues[
                            header.name
                            ].value
                        )
                    )
                for header
                in enums.header.DefaultHeaders
                ]
            )
        )
