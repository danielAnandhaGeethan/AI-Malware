import { useState } from "react";
import axios from "axios";
import { useDropzone } from "react-dropzone";
import { PageLayout } from "../common/components/layouts/PageLayout";

const Upload = () => {
  const [file, setFile] = useState<File>();
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState<number>();

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) {
      alert("Please upload only exe files!");
    } else {
      setFile(acceptedFiles[0]);
    }
  };

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
  });

  const handleSubmit = async () => {
    if (!file) {
      alert("Please upload a file!");
      return;
    }

    setIsLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:8000/upload", formData);

      if (response.status !== 200) {
        throw new Error(`Failed to upload file: ${response.status}`);
      }

      setPrediction(response.data.result);
    } catch (error) {
      console.log(error);
      alert(`Error uploading file`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <PageLayout title="Upload" className="grid place-content-center">
      <div
        {...getRootProps()}
        className="flex flex-col items-center justify-center border-2 border-dashed border-gray-400 rounded-md p-4 text-center"
      >
        <input {...getInputProps()} />
        {file ? (
          <p className="text-lg font-bold">{file.name}</p>
        ) : (
          <>
            <svg
              className="w-12 h-12 text-gray-400"
              fill="currentColor"
              viewBox="0 0 20 20"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                fillRule="evenodd"
                d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
                clipRule="evenodd"
              />
            </svg>
            <p className="text-gray-500 mt-1">
              Drag and drop a file here, or click to select a file
            </p>
          </>
        )}
      </div>

      {prediction !== undefined && (
        <p className="mt-4 text-center">
          Predicted Malware Probability is {prediction}
        </p>
      )}

      <div className="flex justify-center mt-4">
        <button
          className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded ${
            isLoading ? "opacity-50 cursor-not-allowed" : ""
          }`}
          onClick={handleSubmit}
          disabled={isLoading}
        >
          {isLoading ? "Uploading..." : "Submit"}
        </button>
      </div>
    </PageLayout>
  );
};

export default Upload;
