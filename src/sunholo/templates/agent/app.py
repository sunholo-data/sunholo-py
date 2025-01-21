import os

from sunholo.agents import VACRoutes, create_app

from vac_service import vac_stream, vac

app = create_app(__name__)

# Register the Q&A routes with the specific interpreter functions
# creates /vac/<vector_name> and /vac/streaming/<vector_name>
VACRoutes(app, vac_stream, vac)

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)

