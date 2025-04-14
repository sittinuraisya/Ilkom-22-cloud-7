// Struktur awal proyek React dengan fitur manajemen cuti berdasarkan tabel yang diberikan
// Framework: React + Tailwind CSS + Flask sebagai backend (hanya frontend ditampilkan di sini)

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectItem } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Table } from "@/components/ui/table";

export default function Home() {
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Sistem Manajemen Cuti</h1>
      
      <Tabs defaultValue="dashboard">
        <TabsList>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="pengajuan">Pengajuan Cuti</TabsTrigger>
          <TabsTrigger value="admin">Admin Panel</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <Card>
            <CardContent className="space-y-4 p-4">
              <h2 className="text-xl font-semibold">Verifikasi Pengajuan</h2>
              <Table>
                {/* Dummy data pending verifikasi */}
              </Table>
              <Button>Approve</Button>
              <Button variant="destructive">Reject</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pengajuan">
          <Card>
            <CardContent className="space-y-4 p-4">
              <h2 className="text-xl font-semibold">Form Pengajuan Cuti</h2>
              <form className="space-y-4">
                <Input type="date" placeholder="Tanggal Mulai" />
                <Input type="date" placeholder="Tanggal Selesai" />
                <Input type="file" />
                <Button type="submit">Ajukan</Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="admin">
          <Card>
            <CardContent className="space-y-4 p-4">
              <h2 className="text-xl font-semibold">Admin Panel</h2>
              <Select>
                <SelectItem value="periode">Periode</SelectItem>
                <SelectItem value="jabatan">Jabatan</SelectItem>
              </Select>
              <Button>Export CSV</Button>
              <Table>
                {/* Data Rekap */}
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
