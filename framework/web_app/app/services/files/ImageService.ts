export default class ImageService {
    // encodeToBase64 = (imageFile: File): Promise<string> =>
    //     new Promise((resolve, reject) => {
    //         const reader = new FileReader();

    //         reader.onload = () => {
    //             const base64String = reader.result?.toString().split(',')[1] || '';
    //             resolve(base64String);
    //         };

    //         reader.onerror = (error) => {
    //             reject(error);
    //         };

    //         reader.readAsDataURL(imageFile);
    //     });

    decodeBase64Image = (encodedImage: string) => `data:image/jpeg;base64,${encodedImage}`;
}

// const imageService = new ImageService();

// const fileInput = document.getElementById('imageInput') as HTMLInputElement;

// if (fileInput.files && fileInput.files.length > 0) {
//     const imageFile = fileInput.files[0];

//     // Encode to base64
//     const base64String = await imageService.encodeToBase64(imageFile);

//     // Decode back to data URI
//     const dataUri = imageService.decodeBase64Image(base64String);

//     // Now `dataUri` contains the data URI for the image
//     console.log(dataUri);
// }
