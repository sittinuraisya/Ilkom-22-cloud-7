import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const recipes = [
  {
    title: "Salad Quinoa Sehat",
    ingredients: [
      "1 cangkir quinoa",
      "1/2 mentimun, potong dadu",
      "1 buah tomat, potong kecil",
      "2 sdm minyak zaitun",
      "1 sdt air lemon",
      "Garam dan lada secukupnya"
    ],
    steps: [
      "Masak quinoa hingga matang.",
      "Campur semua bahan dalam mangkuk besar.",
      "Aduk rata dan sajikan dingin."
    ]
  },
  {
    title: "Smoothie Pisang Bayam",
    ingredients: [
      "1 buah pisang",
      "1 genggam bayam segar",
      "1 cangkir susu almond",
      "1 sdt madu (opsional)"
    ],
    steps: [
      "Masukkan semua bahan ke dalam blender.",
      "Blender hingga halus.",
      "Tuang ke dalam gelas dan nikmati."
    ]
  },
  {
    title: "Tumis Brokoli dan Tahu",
    ingredients: [
      "100g tahu, potong kotak kecil",
      "1 cangkir brokoli, potong-potong",
      "1 sdm kecap asin rendah sodium",
      "1 sdt minyak wijen",
      "1 siung bawang putih, cincang"
    ],
    steps: [
      "Tumis bawang putih hingga harum.",
      "Masukkan tahu dan brokoli, aduk rata.",
      "Tambahkan kecap dan minyak wijen.",
      "Masak hingga matang dan sajikan."
    ]
  }
];

export default function RecipeApp() {
  const [index, setIndex] = useState(0);
  const recipe = recipes[index];

  const nextRecipe = () => {
    setIndex((index + 1) % recipes.length);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-green-50 p-4">
      <Card className="max-w-md w-full bg-white shadow-lg rounded-2xl p-4">
        <CardContent>
          <h1 className="text-2xl font-bold mb-4 text-green-700">{recipe.title}</h1>
          <h2 className="text-lg font-semibold mb-2">Bahan-bahan:</h2>
          <ul className="list-disc pl-5 mb-4 text-sm">
            {recipe.ingredients.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
          <h2 className="text-lg font-semibold mb-2">Langkah-langkah:</h2>
          <ol className="list-decimal pl-5 text-sm">
            {recipe.steps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
          <div className="mt-6 text-center">
            <Button onClick={nextRecipe} className="bg-green-600 hover:bg-green-700 text-white">
              Resep Selanjutnya
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
