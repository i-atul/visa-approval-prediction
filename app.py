from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_cors import CORS
from src.constants import APP_HOST, APP_PORT, DEBUG
from src.pipeline.prediction_pipeline import visaData, visaClassifier
from src.pipeline.training_pipeline import TrainPipeline

app = Flask(__name__)
CORS(app)

class DataForm:
    def __init__(self, form):
        self.continent = form.get("continent")
        self.education_of_employee = form.get("education_of_employee")
        self.has_job_experience = form.get("has_job_experience")
        self.requires_job_training = form.get("requires_job_training")
        self.no_of_employees = form.get("no_of_employees")
        self.company_age = form.get("company_age")
        self.region_of_employment = form.get("region_of_employment")
        self.prevailing_wage = form.get("prevailing_wage")
        self.unit_of_wage = form.get("unit_of_wage")
        self.full_time_position = form.get("full_time_position")

training_progress = 0

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            form = DataForm(request.form)
            visa_data = visaData(
                continent=form.continent,
                education_of_employee=form.education_of_employee,
                has_job_experience='Y' if form.has_job_experience == 'Yes' else 'N',
                requires_job_training='Y' if form.requires_job_training =='Yes' else 'N',
                no_of_employees=form.no_of_employees,
                company_age=form.company_age,
                region_of_employment=form.region_of_employment,
                prevailing_wage=form.prevailing_wage,
                unit_of_wage=form.unit_of_wage,
                full_time_position='Y' if form.full_time_position == 'Yes' else 'N',
            )
            visa_df = visa_data.get_visa_input_data_frame()
            model_predictor = visaClassifier()
            value = model_predictor.predict(dataframe=visa_df)[0]
            status = "Visa-approved" if value == 1 else "Visa Not-Approved"
            return render_template("index.html", context=status, training_status="", pipeline_stages=[])
        except Exception as e:
            return {"status": False, "error": f"{e}"}
    return render_template("index.html", context="-", training_status="", pipeline_stages=[])

@app.route("/train", methods=["GET"])
def train_route_client():
    return render_template("training.html", training_status="", pipeline_stages=[])

@app.route("/start-training", methods=["GET"])
def start_training():
    global training_progress
    try:
        train_pipeline = TrainPipeline()
        pipeline_stages = []
        pipeline_stages.append("Starting data ingestion...")
        training_progress = 10
        data_ingestion_artifact = train_pipeline.start_data_ingestion()
        pipeline_stages.append("Data ingestion completed.")
        training_progress = 30
        
        pipeline_stages.append("Starting data validation...")
        data_validation_artifact = train_pipeline.start_data_validation(data_ingestion_artifact=data_ingestion_artifact)
        pipeline_stages.append("Data validation completed.")
        training_progress = 50
        
        pipeline_stages.append("Starting data transformation...")
        data_transformation_artifact = train_pipeline.start_data_transformation(
            data_ingestion_artifact=data_ingestion_artifact, data_validation_artifact=data_validation_artifact)
        pipeline_stages.append("Data transformation completed.")
        training_progress = 70
        
        pipeline_stages.append("Starting model training...")
        model_trainer_artifact = train_pipeline.start_model_trainer(data_transformation_artifact=data_transformation_artifact)
        pipeline_stages.append("Model training completed.")
        training_progress = 80
        
        pipeline_stages.append("Starting model evaluation...")
        model_evaluation_artifact = train_pipeline.start_model_evaluation(
            data_ingestion_artifact=data_ingestion_artifact, model_trainer_artifact=model_trainer_artifact)
        pipeline_stages.append("Model evaluation completed.")
        training_progress = 90
        
        if not model_evaluation_artifact.is_model_accepted:
            pipeline_stages.append("Model not accepted.")
            training_progress = 100
            return render_template("training.html", training_status="Model not accepted.", pipeline_stages=pipeline_stages)
        
        pipeline_stages.append("Starting model pushing...")
        model_pusher_artifact = train_pipeline.start_model_pusher(model_evaluation_artifact=model_evaluation_artifact)
        pipeline_stages.append("Model pushing completed.")
        training_progress = 100
        
        return render_template("training.html", training_status="Training successful !!", pipeline_stages=pipeline_stages)
    except Exception as e:
        training_progress = 100
        return render_template("training.html", training_status=f"Error Occurred! {e}", pipeline_stages=[])

@app.route("/training-progress", methods=["GET"])
def training_progress_route():
    global training_progress
    return jsonify({"progress": training_progress})

if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, debug=DEBUG)